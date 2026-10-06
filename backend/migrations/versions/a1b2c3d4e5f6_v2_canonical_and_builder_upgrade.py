"""v2 canonical profile and builder upgrade

Revision ID: a1b2c3d4e5f6
Revises: 26b5d2ef7d67
Create Date: 2026-10-07 01:48:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '26b5d2ef7d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Upgrade resume_versions with v2 builder fields
    with op.batch_alter_table('resume_versions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_version_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('mode', sa.String(50), server_default='clean_rebuild', nullable=True))
        batch_op.add_column(sa.Column('target_job_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('template_id', sa.String(50), server_default='classic', nullable=True))
        batch_op.add_column(sa.Column('is_published', sa.Boolean(), server_default='0', nullable=True))
        batch_op.add_column(sa.Column('ats_loss_score', sa.Float(), server_default='0.0', nullable=True))
        batch_op.add_column(sa.Column('canonical_profile', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('rendered_html', sa.Text(), nullable=True))
        batch_op.create_foreign_key('fk_resume_versions_parent', 'resume_versions', ['parent_version_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_resume_versions_target_job', 'jobs', ['target_job_id'], ['id'], ondelete='SET NULL')

    # 2. Create resume_diff_items table
    op.create_table(
        'resume_diff_items',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('version_id', sa.String(36), sa.ForeignKey('resume_versions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('field_path', sa.String(255), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=True),
        sa.Column('proposed_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(30), server_default='pending', nullable=False),
        sa.Column('edited_text', sa.Text(), nullable=True),
        sa.Column('source', sa.String(50), server_default='ai_suggested_pending', nullable=False),
        sa.Column('evidence_ids', sa.JSON(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('risk_flag', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )

    # 3. Create user_confirmed_facts table
    op.create_table(
        'user_confirmed_facts',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('resume_id', sa.String(36), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('fact_category', sa.String(50), nullable=False),
        sa.Column('field_target', sa.String(100), nullable=True),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('verification_source', sa.String(50), server_default='wizard_answer', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )

    # 4. Create application_tracker table
    op.create_table(
        'application_tracker',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('jobs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('resume_version_id', sa.String(36), sa.ForeignKey('resume_versions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('company', sa.String(255), nullable=False),
        sa.Column('role_title', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), server_default='saved', nullable=False),
        sa.Column('applied_date', sa.DateTime(), nullable=True),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )

    # 5. Create interview_prep_sessions table
    op.create_table(
        'interview_prep_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('job_id', sa.String(36), sa.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('resume_id', sa.String(36), sa.ForeignKey('resumes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('qa_pairs', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('interview_prep_sessions')
    op.drop_table('application_tracker')
    op.drop_table('user_confirmed_facts')
    op.drop_table('resume_diff_items')

    with op.batch_alter_table('resume_versions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_resume_versions_parent', type_='foreignkey')
        batch_op.drop_constraint('fk_resume_versions_target_job', type_='foreignkey')
        batch_op.drop_column('rendered_html')
        batch_op.drop_column('canonical_profile')
        batch_op.drop_column('ats_loss_score')
        batch_op.drop_column('is_published')
        batch_op.drop_column('template_id')
        batch_op.drop_column('target_job_id')
        batch_op.drop_column('mode')
        batch_op.drop_column('parent_version_id')
