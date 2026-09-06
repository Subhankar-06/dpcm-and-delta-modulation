"""
Pulse Code Modulation (PCM) Encoder and Decoder Module.

Performs manual binary word encoding and decoding of quantization indices 
without using external high-level PCM libraries.
"""

import numpy as np
from typing import List

def encode_pcm(indices: np.ndarray, bits: int) -> List[str]:
    """
    Encode an array of integer quantization indices into binary PCM words.

    Parameters
    ----------
    indices : np.ndarray
        Array of integer quantization indices (0 <= index < 2^bits).
    bits : int
        Word length / bit depth (number of bits per sample).

    Returns
    -------
    pcm_words : List[str]
        List of binary strings, each of length exactly `bits`.
        Example: for index = 5, bits = 3 -> '101'.
    """
    pcm_words = []
    for index in indices:
        # Convert integer to binary representation manually using bitwise shifts
        binary_chars = []
        for bit_pos in range(bits - 1, -1, -1):
            bit_val = (int(index) >> bit_pos) & 1
            binary_chars.append(str(bit_val))
        pcm_words.append("".join(binary_chars))
    return pcm_words


def decode_pcm(pcm_words: List[str], bits: int, min_val: float = -1.0, max_val: float = 1.0) -> np.ndarray:
    """
    Decode a list of binary PCM words back to quantized signal values.

    Parameters
    ----------
    pcm_words : List[str]
        List of binary strings of length `bits`.
    bits : int
        Word length / bit depth.
    min_val : float, optional
        Lower dynamic range limit (default -1.0).
    max_val : float, optional
        Upper dynamic range limit (default 1.0).

    Returns
    -------
    quantized_signal : np.ndarray
        Reconstructed quantized signal values.
    indices : np.ndarray
        Reconstructed integer quantization indices.
    """
    L = 2 ** bits
    delta = (max_val - min_val) / L
    
    indices = []
    for word in pcm_words:
        index = 0
        for char in word:
            index = (index << 1) | int(char)
        indices.append(index)
    
    indices_arr = np.array(indices, dtype=int)
    quantized_signal = min_val + (indices_arr + 0.5) * delta
    return quantized_signal, indices_arr
