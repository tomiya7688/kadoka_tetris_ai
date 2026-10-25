cmake_minimum_required(VERSION 3.20)

project(KadokaTetrisAI LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Keep UTF-8 sources and string literals independent of the Windows code page.
if(MSVC)
    add_compile_options(/utf-8)
endif()

option(KADOKA_ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
if(KADOKA_ENABLE_SANITIZERS)
    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang" AND NOT MSVC)
        add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
        add_link_options(-fsanitize=address,undefined)
    else()
        message(FATAL_ERROR "KADOKA_ENABLE_SANITIZERS requires GCC or non-MSVC Clang")
    endif()
endif()

add_library(kadoka_tetris_core
    core/src/active_piece.cpp
    core/src/board.cpp
    core/src/combat_rules.cpp
    core/src/game_state.cpp
    core/src/seven_bag.cpp
    core/src/tetromino.cpp
)

target_include_directories(kadoka_tetris_core
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/core/include
)

target_compile_features(kadoka_tetris_core PUBLIC cxx_std_20)

add_library(kadoka_tetris_runtime
    runtime/src/headless_runtime.cpp
    runtime/src/observation.cpp
)

target_include_directories(kadoka_tetris_runtime
    PUBLIC
        ${CMAKE_CURRENT_SOURCE_DIR}/runtime/include
)

target_link_libraries(kadoka_tetris_runtime PUBLIC kadoka_tetris_core)

target_compile_features(kadoka_tetris_runtime PUBLIC cxx_std_20)

# The learning bridge candidate has no Python headers or runtime dependency.
set_target_properties(kadoka_tetris_core kadoka_tetris_runtime PROPERTIES POSITION_INDEPENDENT_CODE ON)
add_library(kadoka_tetris_bridge SHARED runtime/src/c_api.cpp)
target_compile_definitions(kadoka_tetris_bridge PRIVATE KADOKA_TETRIS_C_API_BUILD)
target_link_libraries(kadoka_tetris_bridge PRIVATE kadoka_tetris_runtime)
target_include_directories(kadoka_tetris_bridge PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/runtime/include)

add_executable(kadoka_tetris_runtime_benchmark
    benchmarks_cpp/headless_runtime_benchmark.cpp
)
target_link_libraries(kadoka_tetris_runtime_benchmark PRIVATE kadoka_tetris_runtime)

include(CTest)

if(BUILD_TESTING)
    # {
    #   責務: [kadoka_add_cpp_test: assert検査を有効にしたC++テストをCTestへ登録する]
    #   処理: [1: 実行ファイルを定義する 2: テストだけでNDEBUGを解除する 3: 必要なlibraryを接続してCTestへ登録する]
    #   引数: [target_name: テスト名 source_file: テストのsource ARGN: 接続するlibraryの一覧]
    #   戻り値: [なし]
    # }
    function(kadoka_add_cpp_test target_name source_file)
        add_executable(${target_name} ${source_file})
        if(MSVC)
            target_compile_options(${target_name} PRIVATE /UNDEBUG)
        else()
            target_compile_options(${target_name} PRIVATE -UNDEBUG)
        endif()
        if(ARGN)
            target_link_libraries(${target_name} PRIVATE ${ARGN})
        endif()
        add_test(NAME ${target_name} COMMAND ${target_name})
    endfunction()

    kadoka_add_cpp_test(kadoka_tetris_assertions_enabled_tests
        tests_cpp/assertions_enabled_test.cpp)
    kadoka_add_cpp_test(kadoka_tetris_c_api_tests tests_cpp/c_api_test.cpp
        kadoka_tetris_bridge kadoka_tetris_runtime)
    kadoka_add_cpp_test(kadoka_tetris_core_tests tests_cpp/core_board_test.cpp
        kadoka_tetris_core)
    kadoka_add_cpp_test(kadoka_tetris_game_state_tests tests_cpp/game_state_test.cpp
        kadoka_tetris_core)
    kadoka_add_cpp_test(kadoka_tetris_headless_runtime_tests tests_cpp/headless_runtime_test.cpp
        kadoka_tetris_runtime)
    kadoka_add_cpp_test(kadoka_tetris_observation_tests tests_cpp/observation_test.cpp
        kadoka_tetris_runtime)

    add_test(
        NAME kadoka_tetris_runtime_benchmark_smoke
        COMMAND kadoka_tetris_runtime_benchmark
            --seed 123
            --games 2
            --ticks 16
            --warmup 1
            --repeats 3
    )
endif()
