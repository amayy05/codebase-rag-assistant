import sys

from graphviz import Digraph

from dependency_tracer import (
    REPO_PATH,
    TARGET_MODULE,
    TARGET_FUNCTION,
    build_function_index,
    build_dependency_graph,
)


FILE_COLORS = {
    "queue.py": "lightblue",
    "queue_engine.py": "lightgoldenrod1",
    "charging_math.py": "lightpink",
    "vehicles.py": "lightgreen",
    "security.py": "plum",
}


def get_file_color(file_path):
    return FILE_COLORS.get(file_path.name, "lightgray")


def find_target_function(function_index, requested_name):

    if requested_name in function_index:
        return requested_name

    matches = [
        qualified_name
        for qualified_name in function_index
        if qualified_name.split(".")[-1] == requested_name
    ]

    if len(matches) == 1:
        return matches[0]

    if len(matches) == 0:
        print(f"\nFunction not found: {requested_name}")
        return None

    print(f"\nMultiple functions found for: {requested_name}")

    for match in matches:
        print(f"  {match}")

    return None


def search_functions(function_index):

    print("\n" + "=" * 50)
    print("RepoMind Function Explorer")
    print("=" * 50)

    keyword = input("\nEnter function name or keyword: ").strip().lower()

    if not keyword:
        print("Search cannot be empty.")
        return None

    matches = [
        function_name
        for function_name in function_index
        if keyword in function_name.lower()
    ]

    if not matches:
        print(f"\nNo functions found matching '{keyword}'.")
        return None

    print("\nMatching functions:")
    print("-" * 50)

    for index, function_name in enumerate(matches, start=1):
        print(f"{index}. {function_name}")

    while True:

        selection = input(
            "\nEnter function number (or 0 to cancel): "
        ).strip()

        if not selection.isdigit():
            print("Please enter a valid number.")
            continue

        selection = int(selection)

        if selection == 0:
            print("Selection cancelled.")
            return None

        if 1 <= selection <= len(matches):
            return matches[selection - 1]

        print("Number out of range. Try again.")


def create_dependency_diagram(graph, function_index, target_name):

    diagram = Digraph(
        name="RepoMind Dependencies",
        format="png",
    )

    diagram.attr(
        rankdir="TB",
        label=f"RepoMind - Dependencies of {target_name}",
        fontsize="20",
        labelloc="b",
    )

    diagram.attr(
        "node",
        shape="box",
        style="rounded,filled",
        fontname="Arial",
    )

    diagram.attr(
        "edge",
        color="gray",
        arrowsize="0.8",
    )

    for function, dependencies in graph.items():

        function_info = function_index[function]

        relative_path = function_info["file"].relative_to(
            REPO_PATH
        ).as_posix()

        label = (
            f"{function_info['name']}\n"
            f"{relative_path}:"
            f"{function_info['line']}"
        )

        diagram.node(
            function,
            label=label,
            fillcolor=get_file_color(function_info["file"]),
        )

        for dependency in dependencies:

            dependency_info = function_index[dependency]

            dependency_path = dependency_info["file"].relative_to(
                REPO_PATH
            ).as_posix()

            dependency_label = (
                f"{dependency_info['name']}\n"
                f"{dependency_path}:"
                f"{dependency_info['line']}"
            )

            diagram.node(
                dependency,
                label=dependency_label,
                fillcolor=get_file_color(dependency_info["file"]),
            )

            diagram.edge(function, dependency)

    function_name = target_name.split(".")[-1]

    output_path = diagram.render(
        filename=f"dependency_graph_{function_name}",
        directory=str(REPO_PATH.parent),
        cleanup=True,
    )

    print("\nDependency diagram created!")
    print(f"Saved at: {output_path}")


def main():

    (
        function_index,
        module_functions,
        import_map,
        module_import_map,
    ) = build_function_index()

    print(f"\nIndexed functions: {len(function_index)}")

    if len(sys.argv) > 1:

        requested_name = sys.argv[1]

        target_name = find_target_function(
            function_index,
            requested_name,
        )

    else:

        target_name = search_functions(function_index)

    if target_name is None:
        return

    print(f"\nSelected function: {target_name}")

    graph = build_dependency_graph(
        target_name,
        function_index,
        import_map,
        module_import_map,
    )

    create_dependency_diagram(
        graph,
        function_index,
        target_name,
    )


if __name__ == "__main__":
    main()