from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_active_session_unique_index'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Detect duplicate ACTIVE sessions before adding the index
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT user_id, array_agg(id) AS ids, COUNT(*) FROM sessions WHERE status = 'ACTIVE' GROUP BY user_id HAVING COUNT(*) > 1")
    )
    duplicates = result.fetchall()
    if duplicates:
        ids = [row[1] for row in duplicates]
        raise Exception(f"Duplicate ACTIVE sessions detected for users. Session ID groups: {ids}")
    # Add partial unique index
    op.create_index(
        'uq_active_session_per_user',
        'sessions',
        ['user_id'],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'")
    )

def downgrade():
    op.drop_index('uq_active_session_per_user', table_name='sessions')
