import os
from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
from datetime import datetime

from backend.database import (
    get_db_connection,
    init_db,
    update_cluster_score
)
from backend.schemas import (
    QuestionCreate,
    QuestionResponse,
    VoteCreate,
    VoteResponse,
    ClusterResponse,
    UserCreate,
    UserResponse
)
from backend.clustering_mock import find_cluster_for_question

# Initialize FastAPI App
app = FastAPI(
    title="Crowd FAQs API",
    description="Backend REST API for Crowd FAQs Platform, developed by Mohd Warish.",
    version="1.0.0"
)

# Enable CORS for frontend compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Initializes the database schema and seeds it on app start."""
    init_db()

# --- Users Endpoints ---

@app.post("/api/users", response_model=UserResponse, tags=["Users"])
def create_user(user: UserCreate):
    """Creates a new user profile in the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM users WHERE id = ?;", (user.id,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="User with this identifier already exists."
            )
        
        cursor.execute(
            "INSERT INTO users (id, username, role) VALUES (?, ?, ?);",
            (user.id, user.username, user.role)
        )
        conn.commit()
        
        cursor.execute("SELECT id, username, role, created_at FROM users WHERE id = ?;", (user.id,))
        row = cursor.fetchone()
        return UserResponse(
            id=row['id'],
            username=row['username'],
            role=row['role'],
            created_at=row['created_at']
        )
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        conn.close()

# --- Questions & Clustering Endpoints ---

@app.post("/api/questions", response_model=QuestionResponse, tags=["Questions"])
def submit_question(question: QuestionCreate):
    """
    Stage 1 & 2: Submit a question, auto-cluster via token-similarity matching, 
    and store in SQLite.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists. If not, auto-create a user to prevent lockouts during testing.
        cursor.execute("SELECT id FROM users WHERE id = ?;", (question.user_identifier,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (id, username, role) VALUES (?, ?, 'user');",
                (question.user_identifier, question.user_identifier.capitalize())
            )
            conn.commit()

        # Step 2: Run Deduplication and Clustering Check
        matched_cluster_id, similarity = find_cluster_for_question(
            conn, question.question_text, question.category
        )

        if matched_cluster_id:
            # Match found! Insert question linked to existing cluster
            cursor.execute("""
                INSERT INTO questions (question_text, category, cluster_id, user_identifier, status)
                VALUES (?, ?, ?, ?, 'pending');
            """, (question.question_text, question.category, matched_cluster_id, question.user_identifier))
            
            question_id = cursor.lastrowid
            conn.commit()
            
            # Recalculate cluster priority score
            update_cluster_score(conn, matched_cluster_id)
            
            cursor.execute("SELECT * FROM questions WHERE id = ?;", (question_id,))
            row = cursor.fetchone()
            return dict(row)
        
        else:
            # No match found! Create a brand new cluster
            cursor.execute("INSERT INTO clusters (representative_question_id) VALUES (NULL);")
            new_cluster_id = cursor.lastrowid
            
            # Insert the new question linked to the brand new cluster
            cursor.execute("""
                INSERT INTO questions (question_text, category, cluster_id, user_identifier, status)
                VALUES (?, ?, ?, ?, 'pending');
            """, (question.question_text, question.category, new_cluster_id, question.user_identifier))
            
            new_question_id = cursor.lastrowid
            
            # Set the representative question ID for the cluster
            cursor.execute("""
                UPDATE clusters 
                SET representative_question_id = ? 
                WHERE id = ?;
            """, (new_question_id, new_cluster_id))
            
            # Generate a mock AI draft answer immediately (Stage 4)
            mock_draft = (
                f"AI Draft Answer: Thank you for your question on {question.category}! "
                f"To address '{question.question_text}', we suggest checking our standard manual. "
                f"Our support agents will soon review and verify this draft."
            )
            cursor.execute("""
                UPDATE clusters 
                SET ai_draft_text = ? 
                WHERE id = ?;
            """, (mock_draft, new_cluster_id))
            
            conn.commit()
            
            # Calculate initial cluster priority score
            update_cluster_score(conn, new_cluster_id)
            
            cursor.execute("SELECT * FROM questions WHERE id = ?;", (new_question_id,))
            row = cursor.fetchone()
            return dict(row)

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during question submission: {str(e)}"
        )
    finally:
        conn.close()

@app.get("/api/questions", response_model=List[ClusterResponse], tags=["Questions"])
def list_questions(
    category: Optional[str] = Query(None, description="Filter clusters by category"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter questions by status ('pending', 'approved', 'rejected')")
):
    """
    Lists all question clusters, including nested questions, 
    sorted by priority score.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Fetch all clusters
        cursor.execute("SELECT * FROM clusters ORDER BY priority_score DESC;")
        cluster_rows = cursor.fetchall()
        
        clusters_list = []
        for crow in cluster_rows:
            cid = crow['id']
            
            # Fetch nested questions for this cluster
            if status_filter:
                cursor.execute(
                    "SELECT * FROM questions WHERE cluster_id = ? AND status = ? ORDER BY created_at DESC;",
                    (cid, status_filter)
                )
            else:
                cursor.execute(
                    "SELECT * FROM questions WHERE cluster_id = ? ORDER BY created_at DESC;",
                    (cid,)
                )
            
            qrows = cursor.fetchall()
            questions = [dict(q) for q in qrows]
            
            # Skip cluster if it has no questions matching the status filter
            if status_filter and not questions:
                continue
                
            # Get representative question text and category
            rep_text = None
            rep_cat = None
            rep_qid = crow['representative_question_id']
            
            if rep_qid:
                cursor.execute("SELECT question_text, category FROM questions WHERE id = ?;", (rep_qid,))
                rep_row = cursor.fetchone()
                if rep_row:
                    rep_text = rep_row['question_text']
                    rep_cat = rep_row['category']
            
            # If no category match, skip when filtering
            if category and rep_cat != category:
                continue

            # Fetch vote count
            cursor.execute("SELECT COUNT(*) FROM votes WHERE cluster_id = ?;", (cid,))
            votes_count = cursor.fetchone()[0]
            
            clusters_list.append(ClusterResponse(
                id=cid,
                representative_question_id=rep_qid,
                representative_text=rep_text,
                category=rep_cat,
                answer_text=crow['answer_text'],
                ai_draft_text=crow['ai_draft_text'],
                priority_score=crow['priority_score'],
                created_at=crow['created_at'],
                votes_count=votes_count,
                questions=questions
            ))
            
        return clusters_list
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during listing: {str(e)}"
        )
    finally:
        conn.close()

# --- Community Voting Endpoints ---

@app.post("/api/votes", response_model=VoteResponse, tags=["Voting"])
def cast_vote(vote: VoteCreate):
    """
    Stage 3: Upvote a question cluster. Enforces unique votes per user 
    per cluster, and dynamically updates the priority score.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if user exists. If not, auto-create to ease testing.
        cursor.execute("SELECT id FROM users WHERE id = ?;", (vote.user_identifier,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (id, username, role) VALUES (?, ?, 'user');",
                (vote.user_identifier, vote.user_identifier.capitalize())
            )
            conn.commit()

        # Check if cluster exists
        cursor.execute("SELECT id FROM clusters WHERE id = ?;", (vote.cluster_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Question cluster {vote.cluster_id} not found."
            )

        # Check for duplicate vote
        cursor.execute(
            "SELECT id FROM votes WHERE cluster_id = ? AND user_identifier = ?;",
            (vote.cluster_id, vote.user_identifier)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already upvoted this question cluster!"
            )

        # Insert vote
        cursor.execute(
            "INSERT INTO votes (cluster_id, user_identifier) VALUES (?, ?);",
            (vote.cluster_id, vote.user_identifier)
        )
        conn.commit()

        # Recalculate priority score dynamically!
        new_score = update_cluster_score(conn, vote.cluster_id)

        return VoteResponse(
            success=True,
            cluster_id=vote.cluster_id,
            new_score=new_score,
            message="Your upvote has been registered successfully!"
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during voting: {str(e)}"
        )
    finally:
        conn.close()

# --- Endpoint to allow updating cluster answers (For Moderation Stage 5 Integration) ---

@app.post("/api/moderation/approve", tags=["Moderation (Integration Support)"])
def approve_cluster(cluster_id: int, answer_text: Optional[str] = None):
    """
    Moderation support helper endpoint. Approves all questions in a cluster 
    and sets the verified answer.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Check cluster
        cursor.execute("SELECT id, ai_draft_text FROM clusters WHERE id = ?;", (cluster_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Cluster not found")
        
        final_answer = answer_text or row['ai_draft_text'] or "Verified by Admin"
        
        # Update answer in cluster
        cursor.execute(
            "UPDATE clusters SET answer_text = ? WHERE id = ?;",
            (final_answer, cluster_id)
        )
        # Update nested questions status to 'approved'
        cursor.execute(
            "UPDATE questions SET status = 'approved' WHERE cluster_id = ?;",
            (cluster_id,)
        )
        conn.commit()
        return {"success": True, "message": f"Cluster {cluster_id} approved and published."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# Mount static folder for the test environment
# Checks if static directory exists; if not, it will be created by static assets setup
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
