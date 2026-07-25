"""
TMF632 Party Management — Pydantic schemas.

Models follow the TMF632 v5 Individual resource specification.
Fields use camelCase aliases to match the TMF JSON wire format,
while Python code uses snake_case internally.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Sub-resources
# ---------------------------------------------------------------------------

class MediumCharacteristic(BaseModel):
    """Contact detail fields — email, phone, or postal address."""
    model_config = ConfigDict(populate_by_name=True)

    city: Optional[str] = None
    contact_type: Optional[str] = Field(None, alias="contactType")
    country: Optional[str] = None
    email_address: Optional[str] = Field(None, alias="emailAddress")
    phone_number: Optional[str] = Field(None, alias="phoneNumber")
    post_code: Optional[str] = Field(None, alias="postCode")
    state_or_province: Optional[str] = Field(None, alias="stateOrProvince")
    street1: Optional[str] = None
    street2: Optional[str] = None


class ContactMedium(BaseModel):
    """A means of contacting a party — wraps MediumCharacteristic."""
    model_config = ConfigDict(populate_by_name=True)

    medium_type: Optional[str] = Field(None, alias="mediumType")
    preferred: Optional[bool] = False
    characteristic: Optional[MediumCharacteristic] = None
    valid_for: Optional[dict] = Field(None, alias="validFor")


class PartyCharacteristic(BaseModel):
    """A key-value pair describing an attribute of the party."""
    model_config = ConfigDict(populate_by_name=True)

    name: str
    value_type: Optional[str] = Field(None, alias="valueType")
    value: str


class RelatedParty(BaseModel):
    """A reference to another party or party role."""
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    referred_type: Optional[str] = Field(None, alias="@referredType")


class ExternalReference(BaseModel):
    """A reference to an external entity such as a CRM record."""
    model_config = ConfigDict(populate_by_name=True)

    external_reference_type: Optional[str] = Field(None, alias="externalReferenceType")
    name: Optional[str] = None
    href: Optional[str] = None


# ---------------------------------------------------------------------------
# Individual — create / update payloads
# ---------------------------------------------------------------------------

class IndividualCreate(BaseModel):
    """
    Payload for POST /individual.

    Only fullName is required — everything else is optional, matching
    the TMF632 specification's flexible create contract.
    """
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    given_name: Optional[str] = Field(None, alias="givenName")
    family_name: Optional[str] = Field(None, alias="familyName")
    full_name: str = Field(..., alias="fullName")
    formatted_name: Optional[str] = Field(None, alias="formattedName")
    gender: Optional[str] = None
    birth_date: Optional[date] = Field(None, alias="birthDate")
    country_of_birth: Optional[str] = Field(None, alias="countryOfBirth")
    nationality: Optional[str] = None
    marital_status: Optional[str] = Field(None, alias="maritalStatus")
    contact_medium: Optional[list[ContactMedium]] = Field(
        default=None, alias="contactMedium"
    )
    party_characteristic: Optional[list[PartyCharacteristic]] = Field(
        default=None, alias="partyCharacteristic"
    )
    related_party: Optional[list[RelatedParty]] = Field(
        default=None, alias="relatedParty"
    )
    external_reference: Optional[list[ExternalReference]] = Field(
        default=None, alias="externalReference"
    )


class IndividualUpdate(BaseModel):
    """
    Payload for PATCH /individual/{id}.

    Every field is optional — only supplied fields are merged.
    """
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = None
    given_name: Optional[str] = Field(None, alias="givenName")
    family_name: Optional[str] = Field(None, alias="familyName")
    full_name: Optional[str] = Field(None, alias="fullName")
    formatted_name: Optional[str] = Field(None, alias="formattedName")
    gender: Optional[str] = None
    birth_date: Optional[date] = Field(None, alias="birthDate")
    country_of_birth: Optional[str] = Field(None, alias="countryOfBirth")
    nationality: Optional[str] = None
    marital_status: Optional[str] = Field(None, alias="maritalStatus")
    contact_medium: Optional[list[ContactMedium]] = Field(
        default=None, alias="contactMedium"
    )
    party_characteristic: Optional[list[PartyCharacteristic]] = Field(
        default=None, alias="partyCharacteristic"
    )
    related_party: Optional[list[RelatedParty]] = Field(
        default=None, alias="relatedParty"
    )
    external_reference: Optional[list[ExternalReference]] = Field(
        default=None, alias="externalReference"
    )


# ---------------------------------------------------------------------------
# Individual — full resource (GET responses)
# ---------------------------------------------------------------------------

class Individual(BaseModel):
    """
    The complete TMF632 Individual resource as returned by GET endpoints.

    Includes server-generated fields: id, href, status, @type, @baseType.
    """
    model_config = ConfigDict(populate_by_name=True)

    id: str
    href: str
    title: Optional[str] = None
    given_name: Optional[str] = Field(None, alias="givenName")
    family_name: Optional[str] = Field(None, alias="familyName")
    full_name: str = Field(..., alias="fullName")
    formatted_name: Optional[str] = Field(None, alias="formattedName")
    gender: Optional[str] = None
    birth_date: Optional[date] = Field(None, alias="birthDate")
    country_of_birth: Optional[str] = Field(None, alias="countryOfBirth")
    nationality: Optional[str] = None
    marital_status: Optional[str] = Field(None, alias="maritalStatus")
    status: str = "initialized"
    contact_medium: Optional[list[ContactMedium]] = Field(
        default=None, alias="contactMedium"
    )
    party_characteristic: Optional[list[PartyCharacteristic]] = Field(
        default=None, alias="partyCharacteristic"
    )
    related_party: Optional[list[RelatedParty]] = Field(
        default=None, alias="relatedParty"
    )
    external_reference: Optional[list[ExternalReference]] = Field(
        default=None, alias="externalReference"
    )
    at_type: str = Field("Individual", alias="@type")
    at_base_type: str = Field("Party", alias="@baseType")
    at_schema_location: Optional[str] = Field(None, alias="@schemaLocation")
