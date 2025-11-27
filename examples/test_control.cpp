int main() {
    int sum = 0;
    for (int i = 0; i < 5; i = i + 1) {
        sum = sum + i;
    }
    int j = 0;
    while (j < 3) {
        j = j + 1;
    }
    do {
        j = j - 1;
    } while (j > 0);

    if (sum > 0) {
        sum = sum - 1;
    } else if (sum == 0) {
        sum = 1;
    } else {
        sum = 2;
    }
    return 0;
}
