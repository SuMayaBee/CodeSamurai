from fastapi import FastAPI, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, asc, desc
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
from typing import List, Union, Optional
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

#SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_async_engine("sqlite+aiosqlite:///./db.sqlite3", connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(engine)


class Base(DeclarativeBase):
    pass



class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author = Column(String)
    genre = Column(String)
    price = Column(Float)


class BookBase(BaseModel):
    id: int
    title: str
    author: str
    genre: str
    price: float

    class Config:
        orm_mode = True

class BookUpdate(BaseModel):
    title: str
    author: str
    genre: str
    price: float



async def get_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    try:
        yield db
    finally:
      await db.close()



app = FastAPI()

# @app.post("/user/")
# async def index(user: UserBase, db: AsyncSession = Depends(get_db)):
#     db_user = User(username=user.username)
#     db.add(db_user)
#     await db.commit()
#     await db.refresh(db_user)
#     return db_user

# # @app.get("/user")
# # async def get_users(db: AsyncSession = Depends(get_db)):
# #     users = db.query(User).all()
# #     return {"users": users}
    

# @app.get("/user")
# async def get_users(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(User))
#     users = result.scalars().all()
#     return {"users": users}



# @app.get("/api/books", response_model=List[BookBase])
# async def get_all_books(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Book).order_by(Book.id))
#     books = result.scalars().all()
#     return {"books": [book._asdict() for book in books]}

################################################################################
@app.post("/api/books", response_model=BookBase)
async def add_book(book: BookBase, db: AsyncSession = Depends(get_db)):
    db_book = Book(id=book.id, title=book.title, author=book.author, genre=book.genre, price=book.price)
    db.add(db_book)
    await db.commit()
    await db.refresh(db_book)
    json_compatible_item_data = jsonable_encoder(db_book)
    return JSONResponse(content=json_compatible_item_data, status_code=201)


@app.put("/api/books/{book_id}", response_model=BookBase)
async def update_book(book_id: int, book: BookUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    db_book = result.scalars().first()
    if db_book is None:
        raise HTTPException(status_code=404, detail=f"Book with id: {book_id} was not found")
    db_book.title = book.title
    db_book.author = book.author
    db_book.genre = book.genre
    db_book.price = book.price
    await db.commit()
    json_compatible_item_data = jsonable_encoder(book)
    return JSONResponse(content=json_compatible_item_data, status_code=200)
    #return Response(status_code=200)



@app.get("/api/books/{book_id}", response_model=BookBase)
async def get_book_by_id(book_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Book).where(Book.id == book_id))
    book = result.scalars().first()
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book with id: {book_id} was not found")
    return book


# @app.get("/api/books")
# async def get_all_books(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Book).order_by(Book.id))
#     books = result.scalars().all()
#     return {"books": books}


@app.get("/api/books")
async def get_all_books(
    db: AsyncSession = Depends(get_db),
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    sort: Optional[str] = None,
    order: Optional[str] = "asc"
):
    query = select(Book)

    if title:
        query = query.filter(Book.title == title)
    if author:
        query = query.filter(Book.author == author)
    if genre:
        query = query.filter(Book.genre == genre)

    if sort:
        if sort.lower() == "title":
            query = query.order_by(asc(Book.title) if order.lower() == "asc" else desc(Book.title))
        elif sort.lower() == "author":
            query = query.order_by(asc(Book.author) if order.lower() == "asc" else desc(Book.author))
        elif sort.lower() == "genre":
            query = query.order_by(asc(Book.genre) if order.lower() == "asc" else desc(Book.genre))
        elif sort.lower() == "price":
            query = query.order_by(asc(Book.price) if order.lower() == "asc" else desc(Book.price))
    else:
        query = query.order_by(asc(Book.id))

    result = await db.execute(query)
    books = result.scalars().all()
    return {"books": books}


