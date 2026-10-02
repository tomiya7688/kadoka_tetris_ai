#include "kadoka/tetris/runtime/headless_runtime.hpp"

#include <algorithm>
#include <charconv>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <limits>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

using kadoka::tetris::PieceType;
using kadoka::tetris::runtime::HeadlessRuntime;
using kadoka::tetris::runtime::PlayerObservation;
using kadoka::tetris::runtime::SemanticAction;
using Clock = std::chrono::steady_clock;

struct Options {
    std::uint64_t seed{1};
    std::size_t games{1};
    std::uint64_t ticks{10000};
    std::size_t warmup{2};
    std::size_t repeats{5};
};

struct Trial {
    double startup_seconds{};
    double observation_seconds{};
    double tick_seconds{};
    double total_seconds{};
    std::uint64_t checksum{14695981039346656037ULL};
};

[[nodiscard]] std::uint64_t parse_integer(std::string_view text, std::string_view name) {
    std::uint64_t value{};
    const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
    if (result.ec != std::errc{} || result.ptr != text.data() + text.size()) {
        throw std::invalid_argument(std::string(name) + " must be an unsigned integer");
    }
    return value;
}

void print_usage() {
    std::cout << "Usage: kadoka_tetris_runtime_benchmark [--seed N] [--games N] "
                 "[--ticks N] [--warmup N] [--repeats N]\n";
}

[[nodiscard]] Options parse_options(int argc, char** argv) {
    Options options;
    for (int index = 1; index < argc; ++index) {
        const std::string_view option(argv[index]);
        if (option == "--help") {
            print_usage();
            std::exit(0);
        }
        if (index + 1 >= argc) {
            throw std::invalid_argument("missing value for " + std::string(option));
        }
        const auto value = parse_integer(argv[++index], option);
        if (option == "--seed") options.seed = value;
        else if (option == "--games") options.games = static_cast<std::size_t>(value);
        else if (option == "--ticks") options.ticks = value;
        else if (option == "--warmup") options.warmup = static_cast<std::size_t>(value);
        else if (option == "--repeats") options.repeats = static_cast<std::size_t>(value);
        else throw std::invalid_argument("unknown option: " + std::string(option));
    }

    if (options.games == 0 || options.games > 64) {
        throw std::invalid_argument("--games must be between 1 and 64");
    }
    if (options.ticks == 0 || options.ticks > 1000000) {
        throw std::invalid_argument("--ticks must be between 1 and 1000000");
    }
    if (options.warmup > 10) {
        throw std::invalid_argument("--warmup must be at most 10");
    }
    if (options.repeats == 0 || options.repeats > 21) {
        throw std::invalid_argument("--repeats must be between 1 and 21");
    }
    if (options.games - 1 > std::numeric_limits<std::uint64_t>::max() - options.seed) {
        throw std::invalid_argument("seed range overflows");
    }
    return options;
}

void hash_integer(std::uint64_t& hash, std::uint64_t value) {
    for (unsigned int byte = 0; byte < 8; ++byte) {
        hash ^= (value >> (byte * 8U)) & 0xffU;
        hash *= 1099511628211ULL;
    }
}

void hash_observation(std::uint64_t& hash, const PlayerObservation& observation) {
    hash_integer(hash, static_cast<std::uint64_t>(observation.board.width));
    hash_integer(hash, static_cast<std::uint64_t>(observation.board.height));
    hash_integer(hash, observation.board.locked_cells.size());
    for (const auto cell : observation.board.locked_cells) {
        hash_integer(hash, static_cast<std::uint64_t>(cell.x));
        hash_integer(hash, static_cast<std::uint64_t>(cell.y));
    }
    hash_integer(hash, observation.board.active_cells.size());
    for (const auto cell : observation.board.active_cells) {
        hash_integer(hash, static_cast<std::uint64_t>(cell.x));
        hash_integer(hash, static_cast<std::uint64_t>(cell.y));
    }

    hash_integer(hash, observation.active_piece.has_value());
    if (observation.active_piece) {
        hash_integer(hash, static_cast<std::uint64_t>(observation.active_piece->kind));
        hash_integer(hash, static_cast<std::uint64_t>(observation.active_piece->x));
        hash_integer(hash, static_cast<std::uint64_t>(observation.active_piece->y));
        hash_integer(hash, static_cast<std::uint64_t>(observation.active_piece->rotation));
    }
    hash_integer(hash, observation.hold_piece.has_value());
    if (observation.hold_piece) {
        hash_integer(hash, static_cast<std::uint64_t>(*observation.hold_piece));
    }
    hash_integer(hash, observation.hold_used);
    hash_integer(hash, observation.next_pieces.size());
    for (const PieceType piece : observation.next_pieces) {
        hash_integer(hash, static_cast<std::uint64_t>(piece));
    }
    hash_integer(hash, observation.game_over);
    hash_integer(hash, static_cast<std::uint64_t>(observation.lines));
    hash_integer(hash, static_cast<std::uint64_t>(observation.combo));
    hash_integer(hash, observation.back_to_back_active);
    hash_integer(hash, observation.pieces_locked);
}

[[nodiscard]] std::vector<SemanticAction> choose_actions(
    const PlayerObservation& observation,
    std::uint64_t tick,
    std::size_t player
) {
    if (observation.game_over || !observation.active_piece) return {};
    const auto choice = (tick + player + observation.pieces_locked) % 7U;
    switch (choice) {
        case 0: return {SemanticAction::MoveLeft};
        case 1: return {SemanticAction::MoveRight};
        case 2: return {SemanticAction::RotateClockwise};
        case 3: return {SemanticAction::RotateCounterClockwise};
        case 4: return {SemanticAction::SoftDrop};
        case 5: return {SemanticAction::HardDrop};
        default: return {SemanticAction::Hold};
    }
}

[[nodiscard]] Trial run_trial(const Options& options) {
    std::vector<std::uint64_t> seeds;
    seeds.reserve(options.games);
    for (std::size_t player = 0; player < options.games; ++player) {
        seeds.push_back(options.seed + player);
    }

    const auto startup_start = Clock::now();
    HeadlessRuntime runtime(seeds);
    const auto startup_end = Clock::now();
    Trial trial;
    trial.startup_seconds = std::chrono::duration<double>(startup_end - startup_start).count();
    const auto total_start = Clock::now();

    std::vector<std::vector<SemanticAction>> proposals(options.games);
    for (std::uint64_t step = 0; step < options.ticks; ++step) {
        for (std::size_t player = 0; player < options.games; ++player) {
            const auto observation_start = Clock::now();
            const PlayerObservation observation = runtime.observe(player);
            trial.observation_seconds += std::chrono::duration<double>(Clock::now() - observation_start).count();
            hash_integer(trial.checksum, step);
            hash_integer(trial.checksum, player);
            hash_observation(trial.checksum, observation);

            proposals[player] = choose_actions(observation, step, player);
            hash_integer(trial.checksum, proposals[player].size());
            for (const auto action : proposals[player]) {
                hash_integer(trial.checksum, static_cast<std::uint64_t>(action));
            }
        }

        const auto tick_start = Clock::now();
        const auto tick = runtime.current_tick();
        for (std::size_t player = 0; player < options.games; ++player) {
            runtime.submit_proposal(player, tick, 0, proposals[player]);
        }
        (void)runtime.advance();
        trial.tick_seconds += std::chrono::duration<double>(Clock::now() - tick_start).count();
    }
    trial.total_seconds = std::chrono::duration<double>(Clock::now() - total_start).count();
    return trial;
}

[[nodiscard]] double median(std::vector<double> values) {
    std::sort(values.begin(), values.end());
    const auto middle = values.size() / 2;
    if (values.size() % 2 != 0) return values[middle];
    return (values[middle - 1] + values[middle]) / 2.0;
}

[[nodiscard]] double rate(double count, double seconds) {
    return seconds > 0.0 ? count / seconds : 0.0;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        const Options options = parse_options(argc, argv);
        for (std::size_t warmup = 0; warmup < options.warmup; ++warmup) {
            (void)run_trial(options);
        }

        std::vector<Trial> trials;
        trials.reserve(options.repeats);
        for (std::size_t repeat = 0; repeat < options.repeats; ++repeat) {
            trials.push_back(run_trial(options));
            if (trials.size() > 1 && trials.back().checksum != trials.front().checksum) {
                throw std::runtime_error("fixed-seed trace checksum changed between repeats");
            }
        }

        std::vector<double> startups;
        std::vector<double> observations;
        std::vector<double> ticks;
        std::vector<double> totals;
        for (const auto& trial : trials) {
            startups.push_back(trial.startup_seconds);
            observations.push_back(trial.observation_seconds);
            ticks.push_back(trial.tick_seconds);
            totals.push_back(trial.total_seconds);
        }

        const double decisions = static_cast<double>(options.games) * static_cast<double>(options.ticks);
        const auto checksum = trials.front().checksum;
        std::cout << std::fixed << std::setprecision(3)
                  << "{\"scope\":\"native_headless_baseline\","
                  << "\"seed\":" << options.seed << ",\"games\":" << options.games
                  << ",\"ticks_per_game\":" << options.ticks
                  << ",\"warmup\":" << options.warmup << ",\"repeats\":" << options.repeats
                  << ",\"median_startup_ms\":" << median(startups) * 1000.0
                  << ",\"median_observations_per_second\":"
                  << rate(decisions, median(observations))
                  << ",\"median_tick_advances_per_second\":"
                  << rate(static_cast<double>(options.ticks), median(ticks))
                  << ",\"median_decision_roundtrips_per_second\":"
                  << rate(decisions, median(totals))
                  << ",\"median_fixed_horizon_episodes_per_second\":"
                  << rate(static_cast<double>(options.games), median(totals))
                  << ",\"trace_checksum\":\"" << std::hex << checksum << "\"}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "benchmark error: " << error.what() << '\n';
        print_usage();
        return 2;
    }
}
