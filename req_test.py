"""
Tests the availability of service over time
"""
import time

import requests

base_url = "http://localhost:8000"

target_endpoints = [
    '/',
    '/resources',
    '/resources/sitemap.xml',
    '/resources/type/exam',
    '/resources/type/schemes_of_work',
    '/resources/type/sitemap.xml',
    '/resources/learning-areas',
    '/resources/learning-areas/creative-arts',
    '/resources/learning-areas/sitemap.xml',
    '/resources/grades',
    '/resources/grades/grade-8',
    '/resources/grades/sitemap.xml',
    '/resources/education-levels',
    '/resources/education-levels/junior-school',
    '/resources/education-levels/sitemap.xml',
    '/accounts/login',
    '/accounts/signup',
    '/accounts/password/reset',
    '/contact',
    '/partners',
]


def calculate_percentage(num1: int, num2: int) -> float:
    percentage = (int(num1) / int(num2) * 100)
    return round(percentage, 2)


start = time.time()
for _ in (range(1, 61)):
    main_count = _
    sub_count = 0
    ok_count = 0
    error_count = 0
    time.sleep(1.5)
    print(f'start at {start}')
    for url in target_endpoints:
        full_target_endpoints_url = f'{base_url}{url}'
        response = requests.get(full_target_endpoints_url)
        time.sleep(4)
        sub_count += 1
        print(
            f'{main_count} - {sub_count} full_target_endpoints_url - {full_target_endpoints_url} returned {response.status_code}')
        ok_count += 1 if response.status_code == 200 else 0
        error_count += 1 if (response.status_code != 200) else 0

    print(
        f'{main_count} - {ok_count}/{sub_count} ok count is {calculate_percentage(ok_count, sub_count)} %'
    )

    print(
        f'{main_count} - {error_count}/{sub_count} error count is {calculate_percentage(error_count, sub_count)} %'
    )

end = time.time()
print(f'end at {end}')
print(f'total time: {end - start}')
