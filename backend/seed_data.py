"""가상의 일별 매출 데이터를 생성해 Firestore data 컬렉션에 저장하는 스크립트.

사용법:
  python seed_data.py               # Firestore에 저장 (FIREBASE_SERVICE_ACCOUNT_JSON 필요)
  python seed_data.py --dry-run     # seed_data.json 파일로만 출력 (Firebase 키 없이 확인용)
  python seed_data.py --count 200   # 생성할 데이터 포인트 개수 지정 (기본 180개, 100개 이상 권장)
"""
import argparse
import json
import random
from datetime import date, timedelta


def generate_points(count: int, start: date) -> list[dict]:
    points = []
    base_value = 4_500_000
    current = start
    for i in range(count):
        trend = i * 15_000
        noise = random.randint(-400_000, 400_000)
        weekend_boost = 300_000 if current.weekday() in (4, 5) else 0
        value = max(0, base_value + trend + noise + weekend_boost)
        memo = random.choice([None, None, None, None, "프로모션", "휴일", "특별 이벤트"])
        points.append({"date": current.isoformat(), "value": value, "memo": memo})
        current += timedelta(days=1)
    return points


def main():
    parser = argparse.ArgumentParser(description="시계열 매출 데이터 시드 스크립트")
    parser.add_argument("--count", type=int, default=180, help="생성할 데이터 포인트 개수 (기본 180)")
    parser.add_argument("--start", type=str, default="2024-07-01", help="시작 날짜 (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Firestore 대신 seed_data.json 파일로 저장")
    args = parser.parse_args()

    start_date = date.fromisoformat(args.start)
    points = generate_points(args.count, start_date)

    if args.dry_run:
        with open("seed_data.json", "w", encoding="utf-8") as f:
            json.dump(points, f, ensure_ascii=False, indent=2)
        print(f"{len(points)}개 데이터 포인트를 seed_data.json 에 저장했습니다.")
        return

    from app.services.firestore_client import get_firestore_client

    db = get_firestore_client()
    collection = db.collection("data")
    batch = db.batch()
    for i, point in enumerate(points):
        batch.set(collection.document(), point)
        if (i + 1) % 400 == 0:
            batch.commit()
            batch = db.batch()
    batch.commit()
    print(f"{len(points)}개 데이터 포인트를 Firestore 'data' 컬렉션에 저장했습니다.")


if __name__ == "__main__":
    main()
