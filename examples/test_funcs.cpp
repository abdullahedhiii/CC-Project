int add(int a, int b) { return a + b; }

int main() {
    int x = add(1, 2);
    int y = add(1); // wrong arity: should be caught by semantic analyzer
    return 0;
}
