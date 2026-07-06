def check_output_formatting(output: str) -> bool:
    """
    Checks if the output meets basic formatting standards.
    Ensures the LLM generated a substantial answer.
    """
    if not output or not isinstance(output, str):
        return False
        
    output = output.strip()
    
    if len(output) < 5:
        # Too short to be a valid detailed answer
        return False
        
    # We could add citation regex checks here if the system strictly requires e.g. [1] format
    # e.g., import re; if not re.search(r'\[\d+\]', output): ...
    
    return True
