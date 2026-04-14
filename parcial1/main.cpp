#include <algorithm>
#include <atomic>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <future>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <optional>
#include <stdexcept>
#include <string>
#include <thread>
#include <utility>
#include <vector>

namespace fs = std::filesystem;

enum class ExecutionType {
    CPU,
    GPU
};

struct DnaComparison {
    std::uint64_t total_differences;
    double time_taken;
    ExecutionType execution_type;
};

struct ChunkLimits {
    std::uint64_t start;
    std::uint64_t end;
};

struct WorkerResult {
    std::string temp_file;
    std::uint64_t diff_count;
    int worker_id;
};

struct ParsedArgs {
    std::string file1;
    std::string file2;
    int workers = 4;
    std::optional<std::string> output;
};

static void print_usage(const char* program_name) {
    std::cerr
        << "Uso: " << program_name
        << " --file1 <ruta> --file2 <ruta> [--workers N] [--output archivo]\n";
}

static std::string json_escape(const std::string& value) {
    std::string escaped;
    escaped.reserve(value.size() + 8);

    for (char ch : value) {
        switch (ch) {
            case '\\':
                escaped += "\\\\";
                break;
            case '"':
                escaped += "\\\"";
                break;
            case '\n':
                escaped += "\\n";
                break;
            case '\r':
                escaped += "\\r";
                break;
            case '\t':
                escaped += "\\t";
                break;
            default:
                escaped += ch;
                break;
        }
    }

    return escaped;
}

static void trim_cr(std::string& line) {
    if (!line.empty() && line.back() == '\r') {
        line.pop_back();
    }
}

static std::uint64_t safe_tellg(std::ifstream& stream, std::uint64_t fallback) {
    const std::streampos position = stream.tellg();
    if (position == std::streampos(-1)) {
        return fallback;
    }

    return static_cast<std::uint64_t>(position);
}

static std::string json_char_or_null(const std::optional<char>& value) {
    if (!value.has_value()) {
        return "null";
    }

    return "\"" + json_escape(std::string(1, *value)) + "\"";
}

static void cleanup_temp_files() {
    for (const auto& entry : fs::directory_iterator(fs::current_path())) {
        if (!entry.is_regular_file()) {
            continue;
        }

        const std::string name = entry.path().filename().string();
        if (name.rfind("temp_", 0) == 0 && entry.path().extension() == ".json") {
            std::error_code ec;
            fs::remove(entry.path(), ec);
        }
    }
}

static std::vector<ChunkLimits> build_line_aligned_chunks(
    const std::string& reference_path,
    std::uint64_t max_file_size,
    std::size_t target_chunk_count
) {
    std::vector<ChunkLimits> chunks;
    if (max_file_size == 0) {
        return chunks;
    }

    std::ifstream reference(reference_path, std::ios::binary);
    if (!reference) {
        throw std::runtime_error("No se pudo abrir el archivo de referencia para dividir chunks.");
    }

    const std::uint64_t chunk_size = (max_file_size / target_chunk_count) + 1;
    std::uint64_t start = 0;

    while (start < max_file_size) {
        std::uint64_t end = std::min(start + chunk_size, max_file_size);
        if (end < max_file_size) {
            reference.clear();
            reference.seekg(static_cast<std::streamoff>(end));

            std::string discard;
            std::getline(reference, discard);

            const std::uint64_t aligned_end = safe_tellg(reference, max_file_size);
            end = aligned_end > start ? aligned_end : max_file_size;
        }

        chunks.push_back({start, end});
        start = end;
    }

    return chunks;
}

static std::uint64_t process_chunk(
    const std::string& file1,
    const std::string& file2,
    ChunkLimits limits,
    std::uint64_t file1_size,
    std::uint64_t file2_size,
    std::ofstream& out,
    bool& first_entry
) {
    if (limits.start == 0) {
        std::cout << "[INFO] Primer worker: Iniciando lectura de la secuencia...\n";
    }

    std::uint64_t diff_count = 0;

    try {
        std::ifstream f1(file1, std::ios::binary);
        std::ifstream f2(file2, std::ios::binary);

        if (!f1 || !f2) {
            throw std::runtime_error("No se pudieron abrir los archivos del chunk.");
        }

        f1.seekg(static_cast<std::streamoff>(limits.start));
        f2.seekg(static_cast<std::streamoff>(limits.start));

        while (safe_tellg(f1, file1_size) < limits.end || safe_tellg(f2, file2_size) < limits.end) {
            std::string line1;
            std::string line2;

            const bool has_line1 = static_cast<bool>(std::getline(f1, line1));
            const bool has_line2 = static_cast<bool>(std::getline(f2, line2));

            if (!has_line1 && !has_line2) {
                break;
            }

            if (has_line1) {
                trim_cr(line1);
            } else {
                line1.clear();
            }

            if (has_line2) {
                trim_cr(line2);
            } else {
                line2.clear();
            }

            if ((!line1.empty() && line1.front() == '>') || (!line2.empty() && line2.front() == '>')) {
                continue;
            }

            const std::uint64_t byte_position = safe_tellg(f1, file1_size);
            const std::size_t max_len = std::max(line1.size(), line2.size());

            for (std::size_t j = 0; j < max_len; ++j) {
                const std::optional<char> char1 = j < line1.size() ? std::optional<char>(line1[j]) : std::nullopt;
                const std::optional<char> char2 = j < line2.size() ? std::optional<char>(line2[j]) : std::nullopt;

                if (char1 != char2) {
                    if (!first_entry) {
                        out << ',';
                    } else {
                        first_entry = false;
                    }

                    out << '['
                        << byte_position
                        << ','
                        << j
                        << ','
                        << json_char_or_null(char1)
                        << ','
                        << json_char_or_null(char2)
                        << ']';

                    ++diff_count;
                }
            }
        }
    } catch (const std::exception& ex) {
        std::cerr << "Error procesando chunk (" << limits.start << ", " << limits.end
                  << "): " << ex.what() << '\n';
    }

    return diff_count;
}

static WorkerResult process_worker(
    const std::string& file1,
    const std::string& file2,
    const std::vector<ChunkLimits>& chunks,
    int worker_id,
    int worker_count,
    std::uint64_t file1_size,
    std::uint64_t file2_size,
    std::atomic<std::size_t>& completed_count,
    std::size_t total_chunks,
    std::mutex& progress_mutex,
    int& last_reported_percent
) {
    const std::string temp_file = "temp_worker_" + std::to_string(worker_id) + ".json";
    std::uint64_t diff_count = 0;
    bool first_entry = true;

    std::ofstream out(temp_file, std::ios::binary);
    if (!out) {
        throw std::runtime_error("No se pudo crear el archivo temporal del worker.");
    }

    out << '[';

    for (std::size_t i = static_cast<std::size_t>(worker_id); i < chunks.size(); i += static_cast<std::size_t>(worker_count)) {
        diff_count += process_chunk(file1, file2, chunks[i], file1_size, file2_size, out, first_entry);

        const std::size_t completed = completed_count.fetch_add(1) + 1;
        const int percent = static_cast<int>((completed * 100) / total_chunks);
        if (percent % 10 == 0) {
            std::lock_guard<std::mutex> lock(progress_mutex);
            if (percent != last_reported_percent) {
                std::cout << "Progreso: " << percent << "% completado...\n";
                last_reported_percent = percent;
            }
        }
    }

    out << ']';
    out.close();

    return {temp_file, diff_count, worker_id};
}

static void merge_temp_json(const std::string& temp_file, std::ofstream& final_json, bool& first_write) {
    if (!fs::exists(temp_file)) {
        return;
    }

    std::ifstream tmp_in(temp_file, std::ios::binary);
    if (!tmp_in) {
        throw std::runtime_error("No se pudo abrir un archivo temporal para consolidar.");
    }

    tmp_in.seekg(0, std::ios::end);
    const std::streamoff file_size = tmp_in.tellg();
    if (file_size > 2) {
        tmp_in.seekg(1, std::ios::beg);

        if (!first_write) {
            final_json << ",\n";
        } else {
            first_write = false;
        }

        std::streamoff remaining = file_size - 2;
        std::vector<char> buffer(1 << 20);

        while (remaining > 0) {
            const std::streamsize to_read = static_cast<std::streamsize>(
                std::min<std::streamoff>(remaining, static_cast<std::streamoff>(buffer.size()))
            );

            tmp_in.read(buffer.data(), to_read);
            const std::streamsize read_count = tmp_in.gcount();
            if (read_count <= 0) {
                throw std::runtime_error("Fallo al leer un archivo temporal durante la consolidacion.");
            }

            final_json.write(buffer.data(), read_count);
            remaining -= read_count;
        }
    }

    tmp_in.close();
    std::error_code ec;
    fs::remove(temp_file, ec);
}

static DnaComparison cpu_calculation(const std::string& path1, const std::string& path2, int num_processes) {
    if (!fs::exists(path1) || !fs::exists(path2)) {
        throw std::runtime_error("Uno de los archivos especificados no existe.");
    }

    if (num_processes <= 0) {
        throw std::runtime_error("El numero de workers debe ser mayor que cero.");
    }

    cleanup_temp_files();

    std::cout << "Iniciando comparacion en paralelo con " << num_processes << " workers...\n";

    const std::uint64_t size1 = fs::file_size(path1);
    const std::uint64_t size2 = fs::file_size(path2);
    const std::uint64_t max_file_size = std::max(size1, size2);

    const std::size_t total_chunks = 100;
    std::vector<ChunkLimits> chunks = build_line_aligned_chunks(path1, max_file_size, total_chunks);

    if (chunks.empty()) {
        std::ofstream final_json("differences.json", std::ios::binary);
        final_json << "[\n\n]\n";
        return {0, 0.0, ExecutionType::CPU};
    }

    using clock = std::chrono::steady_clock;
    const auto start_time = clock::now();

    const int worker_count = std::min<int>(num_processes, static_cast<int>(chunks.size()));
    std::atomic<std::size_t> completed_count{0};
    std::mutex progress_mutex;
    int last_reported_percent = -1;
    std::uint64_t total_differences = 0;

    std::vector<std::future<WorkerResult>> futures;
    futures.reserve(static_cast<std::size_t>(worker_count));

    for (int worker_id = 0; worker_id < worker_count; ++worker_id) {
        futures.push_back(
            std::async(
                std::launch::async,
                process_worker,
                path1,
                path2,
                std::cref(chunks),
                worker_id,
                worker_count,
                size1,
                size2,
                std::ref(completed_count),
                chunks.size(),
                std::ref(progress_mutex),
                std::ref(last_reported_percent)
            )
        );
    }

    std::vector<WorkerResult> worker_results;
    worker_results.reserve(futures.size());
    for (auto& future : futures) {
        worker_results.push_back(future.get());
    }

    std::sort(
        worker_results.begin(),
        worker_results.end(),
        [](const WorkerResult& lhs, const WorkerResult& rhs) {
            return lhs.worker_id < rhs.worker_id;
        }
    );

    std::cout << "\nAbriendo archivo final JSON...\n";
    std::ofstream final_json("differences.json", std::ios::binary);
    if (!final_json) {
        throw std::runtime_error("No se pudo crear differences.json.");
    }

    final_json << "[\n";
    bool first_write = true;
    for (const WorkerResult& result : worker_results) {
        total_differences += result.diff_count;
        merge_temp_json(result.temp_file, final_json, first_write);
    }

    const auto end_time = clock::now();
    final_json << "\n]\n";

    const std::chrono::duration<double> elapsed = end_time - start_time;
    return {total_differences, elapsed.count(), ExecutionType::CPU};
}

static ParsedArgs parse_args(int argc, char* argv[]) {
    ParsedArgs args;

    for (int i = 1; i < argc; ++i) {
        const std::string current = argv[i];

        if (current == "--file1" && i + 1 < argc) {
            args.file1 = argv[++i];
        } else if (current == "--file2" && i + 1 < argc) {
            args.file2 = argv[++i];
        } else if (current == "--workers" && i + 1 < argc) {
            args.workers = std::stoi(argv[++i]);
        } else if (current == "--output" && i + 1 < argc) {
            args.output = argv[++i];
        } else {
            throw std::runtime_error("Argumento invalido o incompleto: " + current);
        }
    }

    if (args.file1.empty() || args.file2.empty()) {
        throw std::runtime_error("Los argumentos --file1 y --file2 son obligatorios.");
    }

    return args;
}

int main(int argc, char* argv[]) {
    try {
        const ParsedArgs args = parse_args(argc, argv);
        const DnaComparison result = cpu_calculation(args.file1, args.file2, args.workers);

        std::cout << "\n" << std::string(40, '=') << '\n';
        std::cout << "RESULTADOS DE LA COMPARACION\n";
        std::cout << std::string(40, '=') << '\n';
        std::cout << "Archivo 1: " << fs::path(args.file1).filename().string() << '\n';
        std::cout << "Archivo 2: " << fs::path(args.file2).filename().string() << '\n';
        std::cout << std::fixed << std::setprecision(4);
        std::cout << "Tiempo total: " << result.time_taken << " segundos\n";
        std::cout << "Total de diferencias: " << result.total_differences << '\n';

        std::ofstream time_json("execution_time.json", std::ios::binary);
        if (!time_json) {
            throw std::runtime_error("No se pudo crear execution_time.json.");
        }

        time_json << "{\n";
        time_json << "    \"file1\": \"" << json_escape(args.file1) << "\",\n";
        time_json << "    \"file2\": \"" << json_escape(args.file2) << "\",\n";
        time_json << "    \"time_taken\": " << std::setprecision(10) << result.time_taken << ",\n";
        time_json << "    \"total_differences\": " << result.total_differences << "\n";
        time_json << "}\n";

        std::cout << "\nArchivos 'differences.json' y 'execution_time.json' generados y actualizados correctamente.\n";
    } catch (const std::exception& ex) {
        cleanup_temp_files();
        print_usage(argv[0]);
        std::cerr << "Error durante la ejecucion: " << ex.what() << '\n';
        return 1;
    }

    return 0;
}
