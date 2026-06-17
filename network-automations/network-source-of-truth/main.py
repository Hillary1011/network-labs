from sqlalchemy import create_engine, String, types, Integer
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column # relationship # (IF multiple tables with relationship are to be implemented)
# from sqlalchemy.exc import IntegrityError
from pydantic import Field 
import uuid 
from pydantic import BaseModel, SecretStr, ConfigDict, field_validator, model_validator
from typing import Annotated, List, Optional

import ipaddress
# Encryption
# try to implement a check that if the application is running for the first time it can 
# check whether .env file exist if not then it can create the Fennet cryptography key 
# to be used in the future POSTs


from fastapi import FastAPI, HTTPException, Request

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# NEWER SQLAlchemy 2.x style:
# from sqlalchemy.orm import Mapped, mapped_column
# from uuid import UUID, uuid4

# class User(Base):
#     __tablename__ = "users"

#     u_id: Mapped[UUID] = mapped_column(
#         primary_key=True,
#         default=uuid4
#     )

#     name: Mapped[str] = mapped_column(String(100))



# Create your database
engine = create_engine("sqlite:///networkDevices.db", echo=False) # connect_args={"check_same_thread":False}
Session = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base = declarative_base()


app = FastAPI(title="Network Device Inventory Manager")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Define DB Models [Network device]
class Device(Base):
    __tablename__ = "Devices"
     # 1. PRIMARY KEY CONSTRAINT
    # Automatically forces uniqueness and NOT NULL constraints.
    device_id: Mapped[uuid.UUID] = mapped_column(
        types.Uuid, 
        primary_key=True, 
        default=uuid.uuid4
    )

    # device_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)  # Column(Integer, primary_key=True, index=True)
    ip: Mapped[String] = mapped_column(String, nullable=False)
    subnet: Mapped[String] = mapped_column(String, nullable=False)
    device_type: Mapped[String] = mapped_column(String) 
    location: Mapped[String] = mapped_column(String)
    vendor: Mapped[String] = mapped_column(String)
    username: Mapped[String] = mapped_column(String)
    line_console: Mapped[String] = mapped_column(String)  # use SecretStr
    previledge_exec: Mapped[String] = mapped_column(String)
    notes: Mapped[String] = mapped_column(String)

    # ip = Column(String, nullable=False)
    # device_type = Column(String)
    # location = Column(String)
    # vendor = Column(String)
    # password = Column(String)     # We may need to stire passwords as Hash 
    # notes = Column(String)

Base.metadata.create_all(engine)

# Define Pydantic Models for data validation
class DeviceBase(BaseModel):
    model_config = ConfigDict(
        strict=True,  # Enable strict mode to enforce type validation
        validate_assignment=True, 
    )

    # Required Fields
    ip: str = Field(..., example="192.168.1.62", description="Management IP address of device")
    subnet: str = Field(..., example="192.168.1.0/24", description="Network subnet")
    device_type: str = Field(..., example="Switch", description="Type of device")
    location: str = Field(..., example="Building A, Floor 2, Room 123, Rack 1", description="Address of device")
    vendor: str = Field(..., example="Cisco", description="Vendor of device")
    username: str = Field(..., example="Hillary", description="User name")

    # Optional Fields
    notes: Optional[str] = Field(..., example="PVSTP & OSPF to be configured!", description="Note")

    # Custom validation for the ip field
    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        try:
            ipaddress.ip_address(value)
        except Exception as e:
            raise e
        # if not ipaddress(value):
        #     raise ValueError("Invalid IP address")
        return value

    # Custom validation for the subnet field
    @field_validator("subnet", mode="after")
    @classmethod
    def validate_subnet(cls, value: str) -> str:
        try:
            ipaddress.ip_network(value)
        except Exception as e:
            raise e 
        return value
    
    # Validate IP address given is within the give subnet
    @model_validator(mode="after")
    def ip_subnet_match(self) -> 'DeviceBase':
        if self.validate_subnet(self.subnet) and self.validate_ip(self.ip):
            if not ipaddress.ip_address(self.ip) in ipaddress.ip_network(self.subnet):
                raise ValueError(f"Given ipaddress {self.ip} does not match subnet {self.subnet}")

        return self
        
    
class DeviceCreate(DeviceBase):
    line_console: Annotated[SecretStr, Field(min_length=6, max_length=12)]
    previledge_exec: Annotated[SecretStr, Field(min_length=6, max_length=12)]

    # Custom validations
    @field_validator("line_console","previledge_exec", mode="before")
    @classmethod
    def validate_password(cls, value:str) -> str:
        # print(f"Entered password is of type: {type(value)}")

        # if isinstance(value, SecretStr):  Will not work!
        #     raise ValueError("Invalid password!")

        if value == "********":
            raise ValueError("Invalid password! Please enter another password")
        return value


class DeviceRespose(DeviceBase):
    device_id: uuid.UUID = Field(..., example="24bc86dd-feef-45ed-8bcd-b4d7dff42e47", description="The unique identifier of device")

    class Config:
        from_attributes = True


class DeviceUpdate(BaseModel):
    ip: Optional[str] = Field(default=None, example="192.168.1.62", description="Management IP address of device")
    subnet: Optional[str] = Field(default=None, example="192.168.1.0/24", description="Network subnet")
    device_type: Optional[str] = Field(default=None, example="Switch", description="Type of device")
    location: Optional[str] = Field(default=None, example="Building A, Floor 2, Room 123, Rack 1", description="Address of device")
    vendor: Optional[str] = Field(default=None, example="Cisco", description="Vendor of device")
    username: Optional[str] = Field(default=None, example="Hillary", description="User name")
    
    notes: Optional[str] = Field(default=None, example="PVSTP & OSPF to be configured!", description="Note")
    line_console: Optional[Annotated[SecretStr, Field(min_length=6, max_length=12)]] = None
    previledge_exec: Optional[Annotated[SecretStr, Field(min_length=6, max_length=12)]] = None

    @field_validator("ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        if not ipaddress(value):
            raise ValueError("Invalid IP address")
        return value


class CredentialResponse(BaseModel):
    username: str = Field(default=None, example="Hillary", description="User name")
    line_console: Annotated[str, Field(example="somecomplexpassword", min_length=6, max_length=12)]
    previledge_exec: Annotated[str, Field(example="somecomplexpassword", min_length=6, max_length=12)]


class DeviceBulkDelete(BaseModel):
    ids: list[uuid.UUID] = Field(..., example='["b4f8f3b3-8e4f...", "8c7a80f4-d67c...", "..."]', description="List IDs of devices to be deleted")

class BulkDeleteResponse(BaseModel):
    deleted_count: int = Field(default=2, example="Hillary", description="User name")
    deleted_ids: list[uuid.UUID] = Field(..., example='["b4f8f3b3-8e4f...", "8c7a80f4-d67c...", "..."]', description="List IDs of deleted devices")

class DeviceFiltersubnet(BaseModel):
    filter_subnets: list[str] =  Field(..., example='["192.168.1.0/24", "172.16.0.0/12"]', description="List subnets of devices to be fetched")

# CREATE UTILITY FUNCTIONS
# def ipaddress(ip: str) -> bool:
#     parts = ip.split('.')

#     # Must have exactly 4 parts
#     if len(parts) != 4:
#         return False

#     for part in parts:
#         # Must contain only digits
#         if not part.isdigit():
#             return False

#         # Convert to integer and check range
#         num = int(part)
#         if num < 0 or num > 255:
#             return False

#     return True

def process_password(credential:str, process:str) -> str:
    """
    process
        'e' - encrypt
        'd' - decrypt
    
    """
    import os
    from cryptography.fernet import Fernet
    from dotenv import load_dotenv

    load_dotenv()

    key = os.getenv("ENCRYPTION_KEY")
    cipher = Fernet(key.encode())
    
    # Encrypting
    if process == "e":
        encrypted_password = cipher.encrypt(credential.encode()).decode()
        return encrypted_password
    elif process == "d":
        password = cipher.decrypt(credential.encode()).decode()
        return password
    else:
        return None

# Create Endpoints GET, POST, PUT, DELETE
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

# GET
@app.get("/devices", response_model=List[DeviceRespose])
def get_all_devices():
    session = Session()
    devices = []
    with session as s:
        devices = s.query(Device).all()
    return devices

@app.get("/device/{device_id}", response_model=DeviceRespose)
def get_device(device_id: uuid.UUID):
    session = Session()
    with session as s:
        device = s.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail=f"Device ID: {device_id} not found")

    return device

@app.get("/device/paswdrecover/{device_id}", response_model=CredentialResponse)
def password_retrieve(device_id: uuid.UUID):
    session = Session()
    with session as s:
        device = s.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            raise HTMLResponse(status_code=404, detail=f"Device ID: {device_id} not found")
    
        # Decrypt the stored passwords
        line_consol_password = process_password(device.line_console, 'd')
        previledge_exec_password = process_password(device.previledge_exec, 'd')
        credentials = CredentialResponse(username=device.username, line_console=line_consol_password, previledge_exec=previledge_exec_password)
    return credentials

# Filter Devices by subnet
# @app.get("/device/paswdrecover/{subnet}", response_model=CredentialResponse) # subnet e,g 24
@app.post("/devices/fetch", response_model=List[DeviceRespose])
def fetch_devices_by_subnet(payload:DeviceFiltersubnet):
    session = Session()
    devices = []
    with session as s:
        devices = (s.query(Device).filter(Device.subnet.in_(payload.filter_subnets)).all())
        # for subnet in payload.filter_subnets:
        #     # print(subnet)
        #     # devices.append(s.query(Device).filter(Device.subnet == subnet).all()) 
        #     devices = s.query(Device).filter(Device.subnet in payload.filter_subnets).all()
    return devices


# POST
@app.post("/device/new_device", response_model=DeviceRespose)
def create_device(device: DeviceCreate):
    session = Session()
    with session as s:
        if s.query(Device).filter(Device.ip == device.ip).first():
            raise HTTPException(status_code=503, detail= f"Device with ip {device.ip} already exist!")
        data = device.model_dump()

        # Encrypt password to be stored in the database
        line_consol_password = process_password(device.line_console.get_secret_value(), 'e')
        previledge_exec_password = process_password(device.previledge_exec.get_secret_value(), 'e')

        data["line_console"] = line_consol_password
        data["previledge_exec"] = previledge_exec_password

        new_device = Device(**data)
        s.add(new_device)
        s.commit()
        s.refresh(new_device) # Required to refresh database atributes required by FastAPI
    return new_device

# PATCH
@app.patch("/device/{device_id}", response_model=DeviceRespose)
def update_device(device_id: uuid.UUID, updated_device:DeviceUpdate):
    session = Session()
    
    with session as s:
        device = s.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            raise HTTPException(status_code=404, detail=f"Device was not found")
        
        data = updated_device.model_dump(exclude_unset=True)
        print(data)
        for field, value in data.items():
            if field == "line_console":
                # Encrypt the updated password fields
                encrypted_password = process_password(updated_device.line_console.get_secret_value(), 'e')
                setattr(device, field, encrypted_password)
            elif field == "previledge_exec":
                encrypted_password = process_password(updated_device.previledge_exec.get_secret_value(), 'e')
                setattr(device, field, encrypted_password)
            else:                
                # print("Attributes set: ", field, value)
                setattr(device, field, value)
        
        s.commit()
        s.refresh(device)
    return device


# DELETE
@app.delete("/device/{device_id}", response_model=DeviceRespose)
def delete_device(device_id: uuid.UUID):
    session = Session()
    
    with session as s:
        device = s.query(Device).filter(Device.device_id == device_id).first()

        if not device:
            raise HTMLResponse(status_code=404, detail="Device not found!")
        
        s.delete(device)
        s.commit()

    return device


@app.delete("/device/", response_model=BulkDeleteResponse)
def delete_bulk(payload: DeviceBulkDelete):
    session = Session()
    with session as s:
        devices = s.query(Device).filter(Device.device_id.in_(payload.ids)).all()
        for device in devices:
            s.delete(device)
        s.commit()

    if len(devices) > 0:
        return BulkDeleteResponse(deleted_count=len(devices), deleted_ids=[device.device_id for device in devices])
  
    return BulkDeleteResponse(deleted_count=0, deleted_ids=[])



# --------------------    
# import uuid

# # 1. Generate a random UUID4 object
# my_uuid = uuid.uuid4()
# print(f"UUID Object: {my_uuid}")