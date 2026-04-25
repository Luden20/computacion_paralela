#include <iostream>
#include <fstream>
#include <string>
#include <cstdint>
#include <filesystem>

using namespace std;

// This function stores the raw ASCII value of each character
uint8_t encode_base(char c) {
    return static_cast<uint8_t>(static_cast<unsigned char>(c));
}

int main(int argc, char* argv[]) {
    // Validate arguments
    if (argc < 2) {
        cerr << "ERROR: missing input file\n";
        cerr << "Usage: fasta_to_bin <input.fna>\n";
        return 1;
    }

    string input_path = argv[1];

    // Validate file exists
    if (!filesystem::exists(input_path)) {
        cerr << "ERROR: file does not exist -> " << input_path << "\n";
        return 1;
    }

    ifstream input_file(input_path);
    if (!input_file.is_open()) {
        cerr << "ERROR: could not open input file\n";
        return 1;
    }

    string output_bin = "dna_matrix.bin";
    string output_meta = "dna_matrix.meta";

    ofstream bin_file(output_bin, ios::binary);
    if (!bin_file.is_open()) {
        cerr << "ERROR: could not create binary output file\n";
        return 1;
    }

    ofstream meta_file(output_meta);
    if (!meta_file.is_open()) {
        cerr << "ERROR: could not create metadata file\n";
        return 1;
    }

    string line;
    uint64_t total_rows = 1;   // Keep Python compatible: matrix with 1 row
    uint64_t total_cols = 0;   // Total number of real DNA chars written

    while (getline(input_file, line)) {
        if (line.empty()) {
            continue;
        }

        if (line[0] == '>') {
            continue;
        }

        for (char c : line) {
            if (c == '\r') {
                continue;
            }
            uint8_t value = encode_base(c);
            bin_file.write(reinterpret_cast<const char*>(&value), sizeof(uint8_t));
            total_cols++;
        }
    }

    if (total_cols == 0) {
        cerr << "ERROR: no valid dna sequence characters were found\n";
        return 1;
    }

    // Metadata: keep same 2-line format expected by Python
    meta_file << total_rows << "\n";
    meta_file << total_cols << "\n";

    input_file.close();
    bin_file.close();
    meta_file.close();

    auto abs_bin = filesystem::absolute(output_bin);
    auto abs_meta = filesystem::absolute(output_meta);

    cout << abs_bin.string() << "\n";
    cout << abs_meta.string() << "\n";

    return 0;
}
