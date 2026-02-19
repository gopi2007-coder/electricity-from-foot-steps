def calculate_points(steps):
    return steps // 100


def load_leaderboard():
    data = {}
    try:
        with open("leaderboard.txt", "r") as f:
            for line in f:
                name, points = line.strip().split(",")
                data[name] = int(points)
    except:
        pass
    return data


def save_leaderboard(data):
    with open("leaderboard.txt", "w") as f:
        for name in data:
            f.write(f"{name},{data[name]}\n")


def show_leaderboard(data):
    print("\n🏆 Leaderboard")
    sorted_users = sorted(data.items(), key=lambda x: x[1], reverse=True)
    for i, (name, points) in enumerate(sorted_users, start=1):
        print(f"{i}. {name} - {points} points")


def menu():
    print("\n1. Add Steps")
    print("2. Check My Points")
    print("3. Show Leaderboard")
    print("4. Exit")


# ---- Start Program ----
leaderboard = load_leaderboard()

username = input("Enter your username: ")

if username not in leaderboard:
    leaderboard[username] = 0

while True:
    menu()
    user = int(input("Choose option: "))

    if user == 1:
        steps = int(input("Enter steps walked: "))

        if steps < 0:
            print("Invalid steps")
            continue

        earned = calculate_points(steps)
        leaderboard[username] += earned

        # Bonus
        if steps >= 8000:
            print("🔥 Bonus 20 points!")
            leaderboard[username] += 20

        save_leaderboard(leaderboard)

        print("You earned:", earned, "points")

    elif user == 2:
        print("Your total points:", leaderboard[username])

    elif user == 3:
        show_leaderboard(leaderboard)

    elif user == 4:
        print("Exiting...")
        break

    else:
        print("Invalid choice")

        

