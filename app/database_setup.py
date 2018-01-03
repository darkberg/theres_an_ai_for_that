import os, sys
from sqlalchemy import Column, ForeignKey, Integer, String, Float, Boolean, DateTime, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine, MetaData

from settings import settings

Base = declarative_base()


class Project(Base):
    __tablename__ = 'project'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    train_credits = Column(Integer)
    test_credits = Column(Integer)

    version_ids = Column(ARRAY(Integer))
    version_id_current = Column(Integer)


class User(Base):
    __tablename__ = 'userbase'

    """
    A user can have multiple projects
    A project contains multiple versions
    """

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    email = Column(String(100), nullable=False)  # Email is username
    password_hash = Column(String(250), nullable=False)
    picture = Column(String(250))

    project_ids = Column(ARRAY(Integer))
    project_id_current = Column(Integer, ForeignKey('project.id'))
    project = relationship(Project)

    def serialize(self):
        user = {
        'name': self.name, 
        'email': self.email,
        'picture': self.picture
        }
        return {'user' : user}


class Machine_learning_settings(Base):
    __tablename__ = 'machine_learning_settings'

    id = Column(Integer, primary_key=True)

    ml_compute_engine_id = Column(Integer, default=0)
    re_train_id = Column(Integer, default=0)
    
    JOB_NAME = Column(String())
    iterations  = Column(Integer)
    previous_goal_iterations = Column(Integer)
    batch_size = Column(Integer)
    trained_checkpoint_prefix = Column(String())
    training_workerCount = Column(Integer)
    training_parameterServerCount = Column(Integer)


class Version(Base):
    __tablename__ = 'version'

    id = Column(Integer, primary_key=True)
    name = Column(String(250))

    labels_number = Column(Integer)

    machine_learning_settings_id = Column(Integer, ForeignKey('machine_learning_settings.id'))
    machine_learning_settings = relationship(Machine_learning_settings)

    train_length = Column(Integer, default=0)
    test_length = Column(Integer, default=0)

    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(Project)

    def serialize(self):
        version = {
        'id': self.id,
        'name': self.name, 
        'labels_number': self.labels_number,
        'train_length': self.train_length,
        'test_length': self.test_length
        }
        return {'version' : version}  


class Image(Base):
    __tablename__ = 'image'

    id = Column(Integer, primary_key=True)
    original_filename = Column(String(250))
    width = Column(Integer)
    height = Column(Integer)
    soft_delete = Column(Boolean, default=False)
    is_test_image = Column(Boolean, default=False)

    url_signed = Column(String())
    url_signed_thumb = Column(String())
    url_signed_expiry = Column(Integer)

    done_labeling = Column(Boolean)

    version_id = Column(Integer, ForeignKey('version.id'))
    version = relationship(Version)

    def serialize(self):
        image = {
        'id': self.id,
        'original_filename': self.original_filename, 
        'width': self.width,
        'height': self.height,
        'soft_delete': self.soft_delete,
        'is_test_image': self.is_test_image,
        'url_signed': self.url_signed,
        'url_signed_thumb': self.url_signed_thumb,
        'version_id': self.version_id,
        'done_labeling' : self.done_labeling,
        }
        return {'image' : image}  


class Label(Base):
    __tablename__ = 'label'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    colour = Column(String(50))
    soft_delete = Column(Boolean)

    project_id = Column(Integer, ForeignKey('project.id'))
    project = relationship(Project)

    def serialize(self):
        label = {
        'id': self.id,
        'name': self.name, 
        'colour': self.colour,
        'soft_delete': self.soft_delete,
        }
        return {'label' : label}   # package it up cleanly


class Box(Base):
    __tablename__ = 'box'

    id = Column(Integer, primary_key=True)

    x_min = Column(Float)
    y_min = Column(Float)
    x_max = Column(Float)
    y_max = Column(Float)
    width = Column(Float)
    height = Column(Float)

    label_id = Column(Integer, ForeignKey('label.id'))
    label = relationship(Label)

    image_id = Column(Integer, ForeignKey('image.id'))
    image = relationship(Image)

    def serialize(self):
        box = {
        'id': self.id,
        'x_min': self.x_min, 
        'y_min': self.y_min,
        'x_max': self.x_max,
        'y_max': self.y_max,
        'image_id' : self.image_id,
        'width' : self.width,
        'height' : self.height,
        }
        return {'box' : box}   # package it up cleanly



if settings.CREATE_TABLES == True:
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(engine)

print("Success")
