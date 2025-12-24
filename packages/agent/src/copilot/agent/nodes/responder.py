"""
Responder Node - Formats the final response to the user.

This is the terminal node that prepares the response
for delivery, adding any necessary context or caveats.
"""

import logging
from typing import Any

from langchain_core.messages import AIMessage

from copilot.agent.state import OutputFormat, ResearchState

logger = logging.getLogger(__name__)


def responder_node(state: ResearchState) -> dict[str, Any]:
    """
    Format and deliver the final response.
    
    This node:
    1. Takes the generated content
    2. Adds any necessary context (quality caveats, etc.)
    3. Formats for the conversation
    
    Returns:
        State updates with final response
    """
    output_content = state.get("output_content", "")
    output_url = state.get("output_url")
    output_format = state.get("output_format", OutputFormat.CHAT.value)
    quality_score = state.get("quality_score", 0.5)
    iteration = state.get("iteration", 1)
    error = state.get("error")
    
    logger.info("💬 Responder: Formatting final response...")
    
    # Handle errors
    if error:
        final_response = (
            f"I encountered an issue while researching your query:\n\n"
            f"**Error:** {error}\n\n"
            f"Please try rephrasing your question or ask about something else."
        )
        return {
            "final_response": final_response,
            "messages": [AIMessage(content=final_response)],
        }
    
    # Handle empty content
    if not output_content:
        final_response = (
            "I wasn't able to generate a meaningful response for your query. "
            "This might be because:\n"
            "• The knowledge graph doesn't contain relevant information\n"
            "• The query needs to be more specific\n\n"
            "Try asking about specific companies, products, or strategies mentioned "
            "in the shareholder documents."
        )
        return {
            "final_response": final_response,
            "messages": [AIMessage(content=final_response)],
        }
    
    # Build the response
    final_response = output_content
    
    # Add URL if we have one
    if output_url:
        final_response += f"\n\n📊 **View presentation:** {output_url}"
    
    # Add quality context for lower-confidence answers
    if quality_score < 0.6:
        final_response += (
            "\n\n---\n"
            "_Note: This analysis is based on limited data. "
            "The knowledge graph may not contain comprehensive information "
            "about all aspects of your query._"
        )
    elif quality_score < 0.75 and iteration > 1:
        final_response += (
            f"\n\n---\n"
            f"_This response was refined over {iteration} iterations to improve accuracy._"
        )
    
    logger.info("   Response ready (%d chars, quality: %.0f%%)", 
               len(final_response), quality_score * 100)
    
    return {
        "final_response": final_response,
        "messages": [AIMessage(content=final_response)],
    }
