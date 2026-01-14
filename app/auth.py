from passlib.context import CryptContext  # 비밀번호 해시 컨텍스트

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # bcrypt 설정


def hash_password(password: str) -> str:  # 비밀번호 해시 함수
    return pwd_context.hash(password)  # 해시된 문자열 반환


def verify_password(password: str, password_hash: str) -> bool:  # 비밀번호 검증 함수
    return pwd_context.verify(password, password_hash)  # 해시 비교 결과 반환
