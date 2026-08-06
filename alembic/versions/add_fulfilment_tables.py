"""add shipment serviceorder service customerbill tables

Revision ID: add_fulfilment_tables
Revises:
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = 'add_fulfilment_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'shipments',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('status', sa.String(64), index=True),
        sa.Column('order_id', sa.String(64), sa.ForeignKey('product_orders.id', ondelete='SET NULL'), index=True),
        sa.Column('tracking_number', sa.String(128), index=True),
        sa.Column('doc', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_table(
        'service_orders',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('state', sa.String(64), index=True),
        sa.Column('order_id', sa.String(64), sa.ForeignKey('product_orders.id', ondelete='SET NULL'), index=True),
        sa.Column('doc', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_table(
        'services',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(255), index=True),
        sa.Column('state', sa.String(64), index=True),
        sa.Column('order_id', sa.String(64), sa.ForeignKey('product_orders.id', ondelete='SET NULL'), index=True),
        sa.Column('customer_id', sa.String(64), sa.ForeignKey('customers.id', ondelete='SET NULL'), index=True),
        sa.Column('doc', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_table(
        'customer_bills',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('state', sa.String(64), index=True),
        sa.Column('billing_account_id', sa.String(64), sa.ForeignKey('billing_accounts.id', ondelete='SET NULL'), index=True),
        sa.Column('order_id', sa.String(64), sa.ForeignKey('product_orders.id', ondelete='SET NULL'), index=True),
        sa.Column('doc', JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('customer_bills')
    op.drop_table('services')
    op.drop_table('service_orders')
    op.drop_table('shipments')
