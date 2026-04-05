"""OpenHands Lab - Streamlit Dashboard."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

# Load .env file
load_dotenv()

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from lab.core import ConfigLoader, SessionManager
from lab.tools import ToolLoader
from lab.utils import EventFormatter, ToolWatcher
from lab.utils.events import FormattedEvent


# Page config
st.set_page_config(
    page_title="OpenHands Lab",
    page_icon="🤖",
    layout="wide",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session" not in st.session_state:
    st.session_state.session = None
if "tool_loader" not in st.session_state:
    st.session_state.tool_loader = None
if "event_formatter" not in st.session_state:
    st.session_state.event_formatter = EventFormatter()


def init_tool_loader() -> ToolLoader:
    """Initialize the tool loader."""
    if st.session_state.tool_loader is None:
        loader = ToolLoader()
        loader.scan_and_load()
        st.session_state.tool_loader = loader
    return st.session_state.tool_loader


def get_config() -> ConfigLoader:
    """Get or create the config loader."""
    return ConfigLoader()


def render_sidebar() -> tuple[str | None, list[str], str]:
    """Render the sidebar with configuration options.

    Returns:
        Tuple of (selected_agent, enabled_tools, workspace_dir)
    """
    st.sidebar.title("🤖 OpenHands Lab")
    st.sidebar.markdown("---")

    config = get_config()

    # Agent selection
    st.sidebar.subheader("Agent")
    agents = list(config.agents.keys())

    if not agents:
        st.sidebar.warning("No agents configured")
        selected_agent = None
    else:
        selected_agent = st.sidebar.selectbox(
            "Select agent",
            options=agents,
            help="Choose a pre-configured playground agent",
        )

        if selected_agent:
            agent = config.agents[selected_agent]
            st.sidebar.caption(agent.description)

    st.sidebar.markdown("---")

    # Tool toggles
    st.sidebar.subheader("Tools")

    # Built-in tools
    builtin_tools = ["terminal", "file_editor", "task_tracker"]
    enabled_tools = []

    st.sidebar.caption("Built-in Tools")
    for tool in builtin_tools:
        if st.sidebar.checkbox(tool, value=True, key=f"tool_{tool}"):
            enabled_tools.append(tool)

    # Custom tools from loader
    loader = init_tool_loader()
    custom_tools = loader.get_tool_info()

    if custom_tools:
        st.sidebar.caption("Custom Tools")
        for tool_info in custom_tools:
            if st.sidebar.checkbox(
                tool_info["name"],
                value=False,
                key=f"tool_{tool_info['name']}",
                help=tool_info["description"],
            ):
                enabled_tools.append(tool_info["name"])

    st.sidebar.markdown("---")

    # Workspace selection
    st.sidebar.subheader("Workspace")
    workspace_dir = st.sidebar.text_input(
        "Working directory",
        value=os.getcwd(),
        help="Directory where the agent will operate",
    )

    # Settings display
    st.sidebar.markdown("---")
    st.sidebar.subheader("Settings")
    settings = config.settings

    st.sidebar.caption(f"Model: {settings.llm.model}")
    st.sidebar.caption(f"Environment: {settings.runtime.environment}")

    # API key check
    api_key = os.getenv(settings.llm.api_key_env)
    if api_key:
        st.sidebar.success("✓ API key configured")
    else:
        st.sidebar.error(f"✗ Missing {settings.llm.api_key_env}")

    return selected_agent, enabled_tools, workspace_dir


def render_thought_stream():
    """Render the thought stream / chat history."""
    st.subheader("💭 Thought Stream")

    # Display message history
    for msg in st.session_state.messages:
        if isinstance(msg, FormattedEvent):
            with st.chat_message(msg.role):
                st.markdown(f"**[{msg.event_type}]** {msg.content}")
        elif isinstance(msg, dict):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            with st.chat_message(role):
                st.markdown(content)


def render_workspace_browser(workspace_dir: str):
    """Render the workspace file browser."""
    st.subheader("📁 Workspace Browser")

    workspace = Path(workspace_dir)
    if not workspace.exists():
        st.warning(f"Workspace does not exist: {workspace_dir}")
        return

    # List files (limited depth)
    try:
        files = []
        for item in workspace.iterdir():
            if item.name.startswith("."):
                continue
            if item.is_file():
                files.append(f"📄 {item.name}")
            elif item.is_dir():
                files.append(f"📁 {item.name}/")

        files.sort()
        if files:
            for f in files[:20]:  # Limit display
                st.text(f)
            if len(files) > 20:
                st.caption(f"... and {len(files) - 20} more items")
        else:
            st.caption("Empty directory")
    except PermissionError:
        st.error("Permission denied")


def handle_user_input(
    agent_name: str,
    enabled_tools: list[str],
    workspace_dir: str,
):
    """Handle user input and run the agent."""
    task = st.chat_input("Enter a task for the agent...")

    if task:
        # Add user message to history
        st.session_state.messages.append({
            "role": "user",
            "content": task,
        })

        # Check for API key
        config = get_config()
        api_key = os.getenv(config.settings.llm.api_key_env)
        if not api_key:
            st.error(f"Please set {config.settings.llm.api_key_env} environment variable")
            return

        # Create session and run
        with st.spinner("Agent is working..."):
            try:
                manager = SessionManager()

                # Event callback to capture events
                def on_event(event):
                    formatted = st.session_state.event_formatter.format(event)
                    st.session_state.messages.append(formatted)

                session = manager.create_session(
                    agent_name=agent_name,
                    workspace_dir=workspace_dir,
                    callbacks=[on_event],
                )

                session.send_message(task)
                session.run()

                # Save trace
                trace_path = session.save_trace()

                st.session_state.messages.append({
                    "role": "system",
                    "content": f"✓ Task completed. Trace saved to: {trace_path}",
                })

            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.messages.append({
                    "role": "system",
                    "content": f"❌ Error: {e}",
                })

        # Force rerun to show new messages
        st.rerun()


def main():
    """Main dashboard entry point."""
    # Sidebar
    agent_name, enabled_tools, workspace_dir = render_sidebar()

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        render_thought_stream()

        if agent_name:
            handle_user_input(agent_name, enabled_tools, workspace_dir)
        else:
            st.info("👈 Select an agent from the sidebar to get started")

    with col2:
        render_workspace_browser(workspace_dir)

    # Clear button
    if st.sidebar.button("Clear History"):
        st.session_state.messages = []
        st.rerun()


if __name__ == "__main__":
    main()
