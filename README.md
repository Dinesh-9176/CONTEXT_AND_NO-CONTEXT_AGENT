# 🤖 My Learning Project: AI Agent Context

This is a simple project I built to learn how AI agents handle memory and context using the **Google ADK**.

## 🧠 What I Learned

In this project, I explored three main ways to help an AI remember things:

1.  **Short-Term Memory**: How the agent keeps track of the current conversation.
2.  **Long-Term Memory**: I learned how to save user facts (like names or interests) into a JSON file so the agent remembers them even if I restart it.
3.  **Compaction**: I learned how to make the agent summarize old parts of a long chat. This keeps the "brain" of the agent from getting too full and slow.

## 👥 The Two Agents

I built two different agents to see the difference:

*   **Context Agent**: This one uses all the memory tricks. It remembers who I am and stays fast in long chats because of "compaction."
*   **No-Context Agent**: This is a basic agent that starts fresh every time. It's my baseline to see how much better the other one is.

## ⚡ My Findings

*   **Memory works!** The Context Agent actually remembers my name and past projects across different sessions.
*   **Speed**: Even though the Context Agent is doing more work, it ended up being **almost 50% faster** in long chats because it keeps the history small and tidy.

## 🛠️ Tools Used
*   Google ADK (Framework)
*   Ollama (Local LLM)
*   Langfuse (To see what's happening inside)
