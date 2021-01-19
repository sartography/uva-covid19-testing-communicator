"""empty message

Revision ID: fa4b41e0bfe6
Revises: d904b7b3c1c0
Create Date: 2020-09-23 14:05:50.766928

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa4b41e0bfe6'
down_revision = 'd904b7b3c1c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ivy_file',
    sa.Column('file_name', sa.String(), nullable=False),
    sa.Column('date_added', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('file_name')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('ivy_file')
    # ### end Alembic commands ###