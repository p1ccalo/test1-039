from sqlalchemy import Table, Column, Integer, String, ForeignKey, Text, DateTime, Date
from sqlalchemy.orm import relationship
from .db import Base
from sqlalchemy import Sequence


client_course = Table(
    "client_course",
    Base.metadata,
    Column("client_id", Integer, ForeignKey("clients.id")),
    Column("course_id", Integer, ForeignKey("courses.id")),
)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, Sequence('clients_id_seq'), primary_key=True, index=True)
    telegram_id = Column(Integer, nullable=True)
    telegram_username = Column(String, nullable=True)
    last_interaction = Column(DateTime, nullable=True)
    phone = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(String, nullable=True)

    client = relationship("Client", back_populates="user", uselist=False)
    admin = relationship("Admin", back_populates="user", uselist=False)


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)

    # --- Симптоми ---
    symptoms = Column(Text, nullable=True)
    symptoms_where = Column(Text, nullable=True)
    symptoms_how_long = Column(Text, nullable=True)
    symptoms_pain_level = Column(Text, nullable=True)
    blood_pressure = Column(Text, nullable=True)

    # --- Дослідження / Огляд ---
    activities = Column(Text, nullable=True)
    research_feet = Column(Text, nullable=True)
    research_knees = Column(Text, nullable=True)
    research_pelvis = Column(Text, nullable=True)
    research_posture = Column(Text, nullable=True)

    # --- Функціональні тести ---
    func_back_thoracic = Column(Text, nullable=True)
    func_back_lumbar = Column(Text, nullable=True)
    func_back_neck = Column(Text, nullable=True)
    func_hips = Column(Text, nullable=True)
    func_knees = Column(Text, nullable=True)
    func_ankles = Column(Text, nullable=True)
    func_feet = Column(Text, nullable=True)
    func_symmetry = Column(Text, nullable=True)
    func_shoulders = Column(Text, nullable=True)
    func_elbows = Column(Text, nullable=True)
    func_wrists = Column(Text, nullable=True)

    # --- Побут / Спосіб життя ---
    work_conditions = Column(Text, nullable=True)
    sport = Column(Text, nullable=True)
    supplements = Column(Text, nullable=True)
    home_devices = Column(Text, nullable=True)

    # --- Висновки та рекомендації ---
    conclusion = Column(Text, nullable=True)
    massage_recommendation = Column(Text, nullable=True)
    insoles = Column(Text, nullable=True)
    preventive_devices = Column(Text, nullable=True)

    # --- Інше ---
    role = Column(String, default="client")
    happies = Column(Integer, default=0)

    # --- Зв'язки ---
    courses = relationship("Course", secondary=client_course, back_populates="clients")
    programs = relationship("Program", back_populates="client")
    photos = relationship("ClientPhoto", back_populates="client")
    user = relationship("User", back_populates="client", uselist=False)


class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, Sequence('admins_id_seq'), primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="admin")

    user = relationship("User", back_populates="admin", uselist=False)



class ClientPhoto(Base):
    __tablename__ = "client_photos"
    id = Column(Integer, Sequence('client_photos_id_seq'), primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    photo_url = Column(String, nullable=False)

    client = relationship("Client", back_populates="photos")

class ExercisePhoto(Base):
    __tablename__ = "exercise_photos"
    id = Column(Integer, Sequence('exercise_photos_id_seq'), primary_key=True, index=True, autoincrement=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    photo_url = Column(String, nullable=False)

    exercise = relationship("Exercise", back_populates="photos")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, Sequence('courses_id_seq'), primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)

    clients = relationship("Client", secondary=client_course, back_populates="courses")
    programs = relationship("Program", back_populates="course")
    exercises = relationship("Exercise", back_populates="course")


class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, Sequence('programs_id_seq'), primary_key=True, index=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    course_id = Column(Integer, ForeignKey("courses.id"))

    client = relationship("Client", back_populates="programs")
    course = relationship("Course", back_populates="programs")
    exercises = relationship("ProgramExercise", back_populates="program")


class Exercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, Sequence('exercises_id_seq'), primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    tags = Column(String)
    description = Column(Text)
    media_url = Column(String)
    course_id = Column(Integer, ForeignKey("courses.id"))

    course = relationship("Course", back_populates="exercises")
    programs = relationship("ProgramExercise", back_populates="exercise")
    photos = relationship("ExercisePhoto", back_populates="exercise")


class ProgramExercise(Base):
    __tablename__ = "program_exercise"
    id = Column(Integer, Sequence('program_exercise_id_seq'), primary_key=True, index=True, autoincrement=True)
    program_id = Column(Integer, ForeignKey("programs.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))

    # нові поля для збереження деталей
    weight = Column(Integer, nullable=True)   # вага
    repeats = Column(Integer, nullable=True)  # повтори
    sets = Column(Integer, nullable=True)     # підходи
    block = Column(Integer, nullable=True)    # номер блоку
    order_num = Column(Integer, nullable=True)  # порядок у блоці

    program = relationship("Program", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="programs")