"""Initial schema creation for Niyog.

Revision ID: 001
Revises:
Create Date: 2026-04-01 00:00:00.000000

Creates all tables:
- companies
- hr_users
- talent_users
- schemas (with JSONB definition, partial unique index for active schema)
- onboarding_sessions
- talent_profiles (with JSONB data)
- files
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create companies table
    op.create_table(
        'companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_companies_slug'),
    )

    # Create hr_users table
    op.create_table(
        'hr_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('api_token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_hr_users_email'),
        sa.UniqueConstraint('api_token', name='uq_hr_users_api_token'),
    )
    op.create_index('idx_hr_users_company', 'hr_users', ['company_id'])

    # Create talent_users table
    op.create_table(
        'talent_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('api_token', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('api_token', name='uq_talent_users_api_token'),
        sa.UniqueConstraint('company_id', 'email', name='uq_talent_users_company_email'),
    )
    op.create_index('idx_talent_users_company', 'talent_users', ['company_id'])

    # Create schemas table
    op.create_table(
        'schemas',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'draft'")),
        sa.Column('definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('hr_thread_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('draft', 'active', 'archived')", name='ck_schema_status'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['hr_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id', 'version', name='uq_schemas_company_version'),
    )
    op.create_index('idx_schemas_company_status', 'schemas', ['company_id', 'status'])
    op.create_index('idx_schemas_definition', 'schemas', ['definition'], postgresql_using='gin')
    # Partial unique index for single active schema per company
    op.execute(
        "CREATE UNIQUE INDEX idx_schemas_single_active ON schemas (company_id) "
        "WHERE status = 'active'"
    )

    # Create onboarding_sessions table
    op.create_table(
        'onboarding_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('talent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schema_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thread_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'in_progress'")),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('in_progress', 'completed', 'abandoned')", name='ck_session_status'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['talent_id'], ['talent_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schema_id'], ['schemas.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('thread_id', name='uq_sessions_thread_id'),
    )
    op.create_index('idx_sessions_talent', 'onboarding_sessions', ['talent_id'])
    op.create_index('idx_sessions_company', 'onboarding_sessions', ['company_id'])

    # Create talent_profiles table
    op.create_table(
        'talent_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('talent_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('schema_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('onboarding_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('is_final', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['talent_id'], ['talent_users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schema_id'], ['schemas.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['onboarding_session_id'], ['onboarding_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_profiles_talent', 'talent_profiles', ['talent_id'])
    op.create_index('idx_profiles_company', 'talent_profiles', ['company_id'])
    op.create_index('idx_profiles_schema', 'talent_profiles', ['schema_id'])
    op.create_index('idx_profiles_data', 'talent_profiles', ['data'], postgresql_using='gin')

    # Create files table
    op.create_table(
        'files',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploader_type', sa.String(50), nullable=False),
        sa.Column('storage_bucket', sa.String(255), nullable=False),
        sa.Column('storage_key', sa.String(500), nullable=False),
        sa.Column('original_name', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('field_key', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['profile_id'], ['talent_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_files_uploader', 'files', ['uploaded_by', 'uploader_type'])
    op.create_index('idx_files_profile', 'files', ['profile_id'])


def downgrade() -> None:
    # Drop all indexes (some need explicit drop)
    op.drop_index('idx_files_profile', 'files')
    op.drop_index('idx_files_uploader', 'files')
    op.drop_table('files')

    op.drop_index('idx_profiles_data', 'talent_profiles')
    op.drop_index('idx_profiles_schema', 'talent_profiles')
    op.drop_index('idx_profiles_company', 'talent_profiles')
    op.drop_index('idx_profiles_talent', 'talent_profiles')
    op.drop_table('talent_profiles')

    op.drop_index('idx_sessions_company', 'onboarding_sessions')
    op.drop_index('idx_sessions_talent', 'onboarding_sessions')
    op.drop_table('onboarding_sessions')

    # Drop partial unique index explicitly
    op.execute('DROP INDEX IF EXISTS idx_schemas_single_active')
    op.drop_index('idx_schemas_definition', 'schemas')
    op.drop_index('idx_schemas_company_status', 'schemas')
    op.drop_table('schemas')

    op.drop_index('idx_talent_users_company', 'talent_users')
    op.drop_table('talent_users')

    op.drop_index('idx_hr_users_company', 'hr_users')
    op.drop_table('hr_users')

    op.drop_table('companies')
