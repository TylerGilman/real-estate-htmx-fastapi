"""Initial schema

Revision ID: 4e9c2c345943
Revises: 
Create Date: 2024-11-05 12:03:14.243489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e9c2c345943'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('brokerages',
    sa.Column('broker_id', sa.Integer(), nullable=False),
    sa.Column('broker_name', sa.String(), nullable=False),
    sa.Column('broker_address', sa.String(), nullable=False),
    sa.Column('broker_phone', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('broker_id')
    )
    op.create_table('clients',
    sa.Column('ssn', sa.String(), nullable=False),
    sa.Column('client_name', sa.String(), nullable=False),
    sa.Column('mailing_address', sa.String(), nullable=False),
    sa.Column('client_phone', sa.String(), nullable=False),
    sa.Column('client_type', sa.Enum('BUYER', 'SELLER', 'LESSEE', name='clienttype'), nullable=False),
    sa.Column('intent', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('ssn')
    )
    op.create_table('properties',
    sa.Column('tax_id', sa.String(), nullable=False),
    sa.Column('property_address', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('price', sa.Float(), nullable=False),
    sa.Column('image_url', sa.String(), nullable=True),
    sa.Column('image_width', sa.Integer(), nullable=True),
    sa.Column('image_height', sa.Integer(), nullable=True),
    sa.Column('property_type', sa.Enum('RESIDENTIAL', 'COMMERCIAL', name='propertytype'), nullable=False),
    sa.PrimaryKeyConstraint('tax_id', 'property_address')
    )
    op.create_table('agents',
    sa.Column('nrds', sa.String(), nullable=False),
    sa.Column('ssn', sa.String(), nullable=False),
    sa.Column('agent_name', sa.String(), nullable=False),
    sa.Column('agent_phone', sa.String(), nullable=False),
    sa.Column('broker_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['broker_id'], ['brokerages.broker_id'], ),
    sa.PrimaryKeyConstraint('nrds'),
    sa.UniqueConstraint('ssn')
    )
    op.create_table('commercial_properties',
    sa.Column('tax_id', sa.String(), nullable=False),
    sa.Column('property_address', sa.String(), nullable=False),
    sa.Column('sqft', sa.Float(), nullable=False),
    sa.Column('industry', sa.String(), nullable=False),
    sa.Column('c_type', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['tax_id', 'property_address'], ['properties.tax_id', 'properties.property_address'], ),
    sa.PrimaryKeyConstraint('tax_id', 'property_address')
    )
    op.create_table('property_client_association',
    sa.Column('tax_id', sa.String(), nullable=False),
    sa.Column('property_address', sa.String(), nullable=False),
    sa.Column('client_ssn', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['client_ssn'], ['clients.ssn'], ),
    sa.ForeignKeyConstraint(['tax_id', 'property_address'], ['properties.tax_id', 'properties.property_address'], ),
    sa.PrimaryKeyConstraint('tax_id', 'property_address', 'client_ssn')
    )
    op.create_table('residential_properties',
    sa.Column('tax_id', sa.String(), nullable=False),
    sa.Column('property_address', sa.String(), nullable=False),
    sa.Column('bedrooms', sa.Integer(), nullable=False),
    sa.Column('bathrooms', sa.Float(), nullable=False),
    sa.Column('r_type', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['tax_id', 'property_address'], ['properties.tax_id', 'properties.property_address'], ),
    sa.PrimaryKeyConstraint('tax_id', 'property_address')
    )
    op.create_table('agent_listings',
    sa.Column('listing_id', sa.Integer(), nullable=False),
    sa.Column('tax_id', sa.String(), nullable=False),
    sa.Column('property_address', sa.String(), nullable=False),
    sa.Column('agent_nrds', sa.String(), nullable=False),
    sa.Column('client_ssn', sa.String(), nullable=False),
    sa.Column('l_agent_role', sa.Enum('BUYER', 'SELLER', 'LESSEE', name='agentrole'), nullable=False),
    sa.Column('listing_date', sa.DateTime(), nullable=True),
    sa.Column('exclusive', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['agent_nrds'], ['agents.nrds'], ),
    sa.ForeignKeyConstraint(['client_ssn'], ['clients.ssn'], ),
    sa.ForeignKeyConstraint(['tax_id', 'property_address'], ['properties.tax_id', 'properties.property_address'], ),
    sa.PrimaryKeyConstraint('listing_id')
    )
    op.create_table('agent_showings',
    sa.Column('showing_id', sa.Integer(), nullable=False),
    sa.Column('tax_id', sa.String(), nullable=False),
    sa.Column('property_address', sa.String(), nullable=False),
    sa.Column('agent_nrds', sa.String(), nullable=False),
    sa.Column('client_ssn', sa.String(), nullable=False),
    sa.Column('s_agent_role', sa.Enum('BUYER', 'SELLER', 'LESSEE', name='agentrole'), nullable=False),
    sa.Column('showing_date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['agent_nrds'], ['agents.nrds'], ),
    sa.ForeignKeyConstraint(['client_ssn'], ['clients.ssn'], ),
    sa.ForeignKeyConstraint(['tax_id', 'property_address'], ['properties.tax_id', 'properties.property_address'], ),
    sa.PrimaryKeyConstraint('showing_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('agent_showings')
    op.drop_table('agent_listings')
    op.drop_table('residential_properties')
    op.drop_table('property_client_association')
    op.drop_table('commercial_properties')
    op.drop_table('agents')
    op.drop_table('properties')
    op.drop_table('clients')
    op.drop_table('brokerages')
    # ### end Alembic commands ###
