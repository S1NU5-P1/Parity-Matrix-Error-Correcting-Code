import random

import bitarray as bitarray
import numpy as np
from bitarray import *

# Stałe wartości, poprawiają czytelność kodu
number_of_parity_bits = 8
number_of_bits_in_byte = 8

# Macierz spełniająca dwa warunki:
# - brak powtarzających się rzędów
# - każdy rząd ma unikalną sumą wszystkich swoich wartości
matrix_H = np.array((
    [1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    [1, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    [0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [1, 1, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0],
    [1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0],
    [0, 1, 1, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0],
    [1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1]
))


class CorrectingError(Exception):
    pass


# Opis oznaczeń w kodzie:
# [UTIL] - samoopisowa, prosta funkcja,
#          istnieje głównie po to, by polepszyć czytelność kodu
# [TEST] - kod napisany wyłącznie w celach testowania programu,
#          nie dodaje żadnej funkcjonalności


# Zakoduj każdy bajt z byte_array
# przekazując go do encode_byte()
# i dodaj na koniec dwa początkowe bajty
def encode_byte_array(byte_array: bytearray):
    result = bytearray()
    for byte in byte_array:
        byte_as_bit_array = byte_to_bit_array(byte)
        encoded_byte = bytearray(encode_byte(byte_as_bit_array).tobytes())
        result.append(encoded_byte[0])
        result.append(encoded_byte[1])
    return result


# Odczytaj co drugi bajt z encoded_byte_array
# i zwróć rezultat
def decode_byte_array(encoded_byte_array: bytearray):
    return encoded_byte_array[::2]

# Odczytaj co drugi bajt z encoded_byte_array
# Połącz razem bit informacji i parzystości jako bitarray
# Popraw wynik za pomocą correct_byte()
# i dodaj dwa pierwsze bajty do wynikowego bajtu
def correct_byte_array(encoded_byte_array: bytearray):
    result = bytearray()
    for i in range(0, len(encoded_byte_array), 2):
        byte_as_bit_array = encoded_byte_to_bit_array(encoded_byte_array[i], encoded_byte_array[i + 1])
        corrected_byte = bytearray(correct_byte(byte_as_bit_array).tobytes())

        result.append(corrected_byte[0])
        result.append(corrected_byte[1])
    return result


# [UTIL]
# Zamień bajt na tablicę bitów
def byte_to_bit_array(byte: int) -> bitarray:
    result = ''
    for i in range(number_of_bits_in_byte):
        result += str(byte % 2)
        byte = int(np.floor(byte / 2))
    return bitarray(result[::-1])


# [UTIL]
# Połącz dwa bajty w jedną tablicę bitów (bitarray)
#   [a, b, c], [d, e, f] -> [a, b, c, d, e, f]
def encoded_byte_to_bit_array(byte_one, byte_two) -> bitarray:
    byte_as_bit_array = bitarray()

    for j in range(number_of_bits_in_byte):
        byte_as_bit_array.append(byte_to_bit_array(byte_one)[j])

    for j in range(number_of_parity_bits):
        byte_as_bit_array.append(byte_to_bit_array(byte_two)[j])

    return byte_as_bit_array


# Zakoduj bajt, dodając do niego bajt parzystości:
# Weź wycinek matrix_H o liczbie kolumn równej number_of_parity_bits
# Oblicz bit parzystości:
#   (hamming_matrix * T(word_array)) % 2
# i ostatecznie połącz bit zawierający informację i bit parzystości
#   [a, b, c], [d, e, f] -> [a, b, c, d, e, f]
# Zwróć rezultat
def encode_byte(one_byte: bitarray) -> bitarray:
    hamming_matrix = matrix_H[0:, :number_of_parity_bits]
    word_array = bit_array_to_vector(one_byte)

    parity_byte = hamming_matrix.dot(word_array.T)
    parity_byte %= 2

    encoded_byte = bitarray()
    for i in range(number_of_bits_in_byte):
        encoded_byte.append(word_array[i])

    for i in range(number_of_parity_bits):
        encoded_byte.append(parity_byte[i])

    return encoded_byte


# [UTIL]
# zamień tablicę bitów (bitarray) na np.array 
# zawierającą bity przekonwertowane na inty
def bit_array_to_vector(bits: bitarray) -> np.ndarray:
    result = []
    for i in range(len(bits)):
        result.append(int(bits[i]))
    return np.array(result)


# Oblicz:
#   matrix_H * np.array(coded_byte) % 2
# Zwróć wiersz, który powinien się równać
# jednemu z wierszy matrix_H
def calculate_syndrome(coded_byte) -> np.ndarray:
    syndrome_array = bit_array_to_vector(coded_byte)
    result: np.ndarray = matrix_H.dot(syndrome_array)
    return result % 2


# [UTIL]
# zwraca True jeżeli nie ma jedynek w tablicy
def check_coded_byte(syndrome: np.ndarray) -> bool:
    return np.count_nonzero(syndrome) == 0

# Oblicz syndrom coded_byte
# i spróbuj go naprawić
def correct_byte(coded_byte: bitarray):
    syndrome = calculate_syndrome(coded_byte)
    coded_byte_copy = coded_byte.copy()

    if check_coded_byte(syndrome):
        return coded_byte

    try:
        return try_correct_one_bit(coded_byte_copy, syndrome)
    except CorrectingError:
        pass
    try:
        return try_correct_two_bits(coded_byte_copy, syndrome)
    except CorrectingError:
        raise CorrectingError()

# Sprawdź czy wektor syndromu
#  ma odpowiadającą jej kolumnę w T(matrix_H)
# Jeżeli tak, zamień bit na pozycji odpowiadającej numerowi kolumny
# w przeciwnym razie zwróć wyjątek (więcej niż jeden bit uległ przekształceniu)
def try_correct_one_bit(coded_byte: bitarray, syndrome: np.ndarray):
    i = 0
    for column in matrix_H.T:
        # Sprawdź czy odpowiednie wartości syndromu i kolumny
        # są sobie równe
        if np.equal(syndrome, column).all():
            coded_byte[i] ^= 1
            return coded_byte
        i += i

    raise CorrectingError()


# Funkcja dodaje do siebie dwie różne kolumny T(matrix_H)
#  upewniając się, że każdy element ma wartość 0 lub 1
# Jeżeli syndrom i suma kolumn są ze sobą identyczne,
#  bity na pozycjach odpowiadających numerom kolumn są poprawione
# W przeciwnym razie zwróć wyjątek (więcej niż dwa bity uległy przekształceniu)
def try_correct_two_bits(coded_byte: bitarray, syndrome: np.ndarray):
    i = 0
    j = 0
    for column in matrix_H.T:
        for column2 in matrix_H.T:
            if i == j:
                continue

            sum_of_two_columns = (column + column2) % 2
            if np.equal(sum_of_two_columns, syndrome).all():
                coded_byte[i] ^= 1
                coded_byte[j] ^= 1
                return coded_byte
            j += 1
        i += 1
        j = 0

    raise CorrectingError()


# [UTIL]
# Zwróć pierwsze 8 bitów z tablicy bitów (bitarray)
def decode_byte(coded_byte: bitarray) -> bitarray:
    return coded_byte[:8]



# [TEST]
# Zasymuluj uszkodzenie danych w transmisji
def corrupt_byte_array(encoded_byte_array: bytearray, corrupted_percentage: float):
    result = encoded_byte_array.copy()

    result = bytearray()
    for i in range(0, len(encoded_byte_array), 2):
        corrupted_byte = encoded_byte_array[i:i+2]
        if random.random() <= (corrupted_percentage / 100):
            byte_as_bit_array = encoded_byte_to_bit_array(encoded_byte_array[i], encoded_byte_array[i + 1])
            corrupted_byte = bytearray(simulate_noise(byte_as_bit_array, 2).tobytes())

        result.append(corrupted_byte[0])
        result.append(corrupted_byte[1])
    return result


# [TEST], [UTIL]
# Funkcja pomocnicza dla corrupt_byte_array()
# Symuluje uszkodzenie bajtu, zmieniając
# wartości bitów w coded_byte w ilości
# podanej w number_of_switched_bytes
def simulate_noise(coded_byte: bitarray, number_of_switched_bits: int):
    result = coded_byte.copy()

    coded_byte_range = range(0, number_of_parity_bits + number_of_bits_in_byte - 1)
    switched_bits_indexes = random.sample(coded_byte_range, number_of_switched_bits)
    for i in switched_bits_indexes:
        result[i] ^= 1
    return result
