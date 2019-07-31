import string
import random


def random_string(length: int):
    return "".join(random.choice(string.ascii_letters + string.digits) for i in range(length))


if __name__ == '__main__':

    print("Введите количество команд: ")

    n = int(input())
    teams = []
    for t in range(n):
        teams.append({
            "user_id": "",
            "name": "",
            "password": random_string(5),
            "point": -1
        })

    print(teams)
    with open('teams.json', 'w') as file:
        file.write(str(teams).replace("'", '"'))
