from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain_core.tools import tool

import docker

# Docker client
def get_docker_client():
    try:
        return docker.from_env()
    except Exception as e:
        raise RuntimeError(
            f"Could not connect to Docker daemon. Is Docker running? Error: {e}"
        )


# Tools the agent can call
@tool
def list_running_containers() -> str:
    """List all currently running Docker containers with their ID, name,
    image, status, and exposed ports. Use this whenever the user asks what
    containers are running."""
    client = get_docker_client()
    containers = client.containers.list(all=False)  # only running containers

    if not containers:
        return "No running containers found."

    lines = []
    for c in containers:
        ports = c.attrs.get("NetworkSettings", {}).get("Ports", {})
        port_str = ", ".join(ports.keys()) if ports else "none"
        lines.append(
            f"- ID: {c.short_id} | Name: {c.name} | Image: {c.image.tags} "
            f"| Status: {c.status} | Ports: {port_str}"
        )
    return "\n".join(lines)


@tool
def list_all_containers() -> str:
    """List ALL Docker containers (running and stopped), with their status.
    Use this if the user asks about stopped/exited containers too."""
    client = get_docker_client()
    containers = client.containers.list(all=True)

    if not containers:
        return "No containers found (running or stopped)."

    lines = [
        f"- ID: {c.short_id} | Name: {c.name} | Image: {c.image.tags} | Status: {c.status}"
        for c in containers
    ]
    return "\n".join(lines)


@tool
def get_container_logs(container_name_or_id: str, tail: int = 20) -> str:
    """Get the last N log lines (default 20) for a specific container,
    identified by its name or ID."""
    client = get_docker_client()
    try:
        container = client.containers.get(container_name_or_id)
    except docker.errors.NotFound:
        return f"No container found with name/ID '{container_name_or_id}'."

    logs = container.logs(tail=tail).decode("utf-8", errors="replace")
    return logs or "(no logs)"


@tool
def get_container_stats(container_name_or_id: str) -> str:
    """Get a snapshot of resource usage (CPU %, memory usage) for a
    specific running container, identified by its name or ID."""
    client = get_docker_client()
    try:
        container = client.containers.get(container_name_or_id)
    except docker.errors.NotFound:
        return f"No container found with name/ID '{container_name_or_id}'."

    if container.status != "running":
        return f"Container '{container_name_or_id}' is not running (status: {container.status})."

    stats = container.stats(stream=False)

    # CPU % calculation
    cpu_delta = (
        stats["cpu_stats"]["cpu_usage"]["total_usage"]
        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
    )
    system_delta = (
        stats["cpu_stats"]["system_cpu_usage"]
        - stats["precpu_stats"]["system_cpu_usage"]
    )
    num_cpus = stats["cpu_stats"].get("online_cpus", 1)
    cpu_percent = 0.0
    if system_delta > 0 and cpu_delta > 0:
        cpu_percent = (cpu_delta / system_delta) * num_cpus * 100.0

    mem_usage = stats["memory_stats"].get("usage", 0) / (1024 ** 2)
    mem_limit = stats["memory_stats"].get("limit", 0) / (1024 ** 2)

    return (
        f"CPU: {cpu_percent:.2f}% | "
        f"Memory: {mem_usage:.1f} MiB / {mem_limit:.1f} MiB"
    )


TOOLS = [
    list_running_containers,
    list_all_containers,
    get_container_logs,
    get_container_stats,
]


# Agent setup
SYSTEM_PROMPT = (
    "You are a helpful DevOps assistant with access to tools for "
    "inspecting Docker containers on the user's machine. Use the "
    "tools to get real, up-to-date information rather than "
    "guessing. Be concise and format lists clearly."
)


def build_agent(model_name: str = "qwen2.5", base_url: str = "http://localhost:11434"):
    llm = ChatOllama(model=model_name, base_url=base_url, temperature=0)
    agent = create_agent(llm, tools=TOOLS, system_prompt=SYSTEM_PROMPT)
    return agent


def main():
    print("Docker Inspector Agent (Qwen via Ollama)")
    print("Type 'exit' to quit.\n")

    agent = build_agent()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        # The last message in the returned state is the agent's final reply
        final_message = result["messages"][-1]
        content = getattr(final_message, "content", final_message)
        print(f"\nAgent: {content}\n")


if __name__ == "__main__":
    main()