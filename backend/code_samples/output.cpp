#include <iostream>
#include <cctype>
#include <algorithm>
#include <string>
using namespace std;

int main() {
    cout << "Enter your name: ";
    string name;
    cin >> name;
    cout << (transform(name.begin(), name.end(), name.begin(), ::toupper), name) << endl;
    return 0;
}
