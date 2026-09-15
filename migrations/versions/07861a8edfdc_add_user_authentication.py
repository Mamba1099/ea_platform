from alembic import op
import sqlalchemy as sa


revision = "07861a8edfdc"
down_revision = "3e859849df27"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",

        sa.Column(
            "id",
            sa.BigInteger(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "username",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "password_hash",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "role",
            sa.String(length=32),
            nullable=False,
            server_default="ADMIN",
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "last_login_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_username",
        "users",
        ["username"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_users_username",
        table_name="users",
    )

    op.drop_table("users")