'''
home_library_v4 / tests/test_db.py
-----------------------------------------------
GitHub Actions DB 연동 테스트 (v5 2차 세션)

- test.yml의 services.postgres가 띄워준 임시 DB에 실제로 접속해서
  Book 모델이 저장/조회되는지 확인한다.
- DATABASE_URL은 test.yml에서 CI 전용 값으로 주입되므로,
  이 파일 안에는 접속 정보가 전혀 하드코딩되지 않는다.
- /books/lookup처럼 국립중앙도서관 API를 부르는 부분은 일부러 건드리지 않는다
  (API 키가 CI에는 없다). 대신 우리가 직접 통제할 수 있는 "DB 저장" 부분만 검증한다.
'''
from database import Base, engine, SessionLocal
from models import Book


def test_책을_저장하고_다시_조회할_수_있다():
    # 매 실행마다 완전히 빈 DB이므로, 먼저 테이블부터 만들어야 한다.
    # 로컬에서는 main.py가 이미 만들어둔 테이블을 그대로 쓰지만,
    # CI는 항상 "방금 태어난 빈 DB"라서 이 한 줄이 없으면 "테이블 없음" 에러가 난다.
    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        # models.py의 Book: title(필수), isbn/author/publisher(선택), 등록.
        book = Book(title='CI 테스트용 책', isbn='9999999999999', author='테스트 저자')
        db.add(book)
        db.commit()
        db.refresh(book)  # DB가 자동으로 채운 id, created_at 등을 다시 읽어온다.

        saved = db.get(Book, book.id)
        assert saved is not None
        assert saved.title == 'CI 테스트용 책'
        # models.py에서 default='confirmed'로 정의된 값이 실제로 DB에도 반영됐는지 확인.
        # 이건 "파이썬 코드상의 기본값"이 아니라 "진짜 DB에 저장된 값"을 검증하는 것이라
        # 순수 함수 테스트(1장)와는 성격이 다르다.
        assert saved.recognition_status == 'confirmed'
    finally:
        # CI 컨테이너는 job이 끝나면 어차피 통째로 폐기되지만,
        # "테스트는 자기가 만든 데이터를 스스로 치운다"는 습관을 들이는 차원에서 정리한다.
        db.query(Book).delete()
        db.commit()
        db.close()