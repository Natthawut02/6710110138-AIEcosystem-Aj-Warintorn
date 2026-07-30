from fastapi import APIRouter, Depends
from app.models.schemas import UserOut
from app.db.models import User
from app.core.deps import get_current_user, get_current_admin_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current logged-in user details.
    """
    return current_user


@router.get("/admin-only")
def read_admin_only(current_user: User = Depends(get_current_admin_user)):
    """
    Get admin-only resource. Restricted to users with 'admin' role.
    """
    return {
        "message": "Welcome Admin! You have access to restricted resources.",
        "admin": current_user.username,
        "role": current_user.role
    }
