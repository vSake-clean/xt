import chess
FEN = '3k4/7R/2nb1n2/pr2qb2/3r1p2/1pp5/3n4/K7 w - - 0 1'
KR = [('c8','c7'),('b8','b7'),('a8','a7'),('b8','b7'),('c8','c7'),('d8','d7'),('e8','e7'),('f8','f7'),('g8','g7'),('h8','g8'),
      ('h7','g7'),('h6','g6'),('h5','g5'),('h4','g4'),('h3','g3'),('h2','g2'),('h1','h2'),('g1','g2'),('f1','f2'),('e1','e2'),
      ('f1','f2'),('g1','g2'),('h1','g1'),('h2','g2'),('h3','g3'),('h4','g4'),('h5','g5'),('h6','g6'),('h7','g7'),('h8','h7'),
      ('g8','g7'),('f8','f7'),('e8','e7'),('d8','d7'),('c8','c7'),('b8','b7'),('a8','a7'),('b8','b7'),('c8','c7'),('d8','d7'),
      ('e8','e7'),('f8','f7'),('g8','g7'),('h8','g8'),('h7','g7'),('h6','g6'),('h5','g5'),('h4','g4')]
KT = [0.17,0.77,1.23,1.67,2.10,2.60,3.10,3.50,3.90,4.30,4.67,5.03,5.40,5.80,6.10,6.47,6.83,7.17,7.50,7.83,8.20,8.57,8.93,9.30,
      9.63,10.00,10.37,10.70,11.07,11.40,11.73,12.07,12.40,12.70,13.00,13.27,13.57,13.87,14.17,14.50,14.80,15.10,15.40,15.73,
      16.07,16.40,16.73,17.07]
RT = [0.47,1.00,1.47,1.87,2.33,2.90,3.30,3.70,4.10,4.47,4.87,5.23,5.60,5.97,6.27,6.63,6.97,7.33,7.67,8.03,8.37,8.73,9.10,9.47,
      9.83,10.17,10.53,10.87,11.23,11.57,11.90,12.23,12.53,12.85,13.13,13.43,13.73,14.03,14.33,14.63,14.97,15.27,15.57,15.90,
      16.20,16.53,16.87,17.20]
BRILLIANT = {14,15,16,17,18,20,21,25,27,28,44,45,46}
BEST_ROOK = {9,22,29}

def build():
    b = chess.Board(FEN)
    assert b.is_valid(), b.status()
    seq = []   # (time, from, to, piece_symbol, cls)
    first = chess.Move.from_uci('h7d7')
    assert first in b.legal_moves
    b.push(first); assert b.is_check()
    start_fen = b.fen()
    # capturing the rook must be stalemate
    def stalemate_if_taken(bd):
        for mv in bd.legal_moves:
            if bd.piece_at(mv.to_square) and bd.piece_at(mv.to_square).piece_type == chess.ROOK and bd.piece_at(mv.to_square).color == chess.WHITE:
                bd.push(mv); ok = bd.is_stalemate(); bd.pop()
                if not ok: return False
        return True
    assert stalemate_if_taken(b)
    rook_sq = 'd7'; king_sq = 'd8'
    for i, (k, r) in enumerate(KR):
        mv = chess.Move.from_uci(king_sq + k)
        assert mv in b.legal_moves, (i, 'king', king_sq, k, b.fen())
        b.push(mv); seq.append((KT[i], king_sq, k, 'k', 'best')); king_sq = k
        mv = chess.Move.from_uci(rook_sq + r)
        assert mv in b.legal_moves, (i, 'rook', rook_sq, r, b.fen())
        b.push(mv)
        assert b.is_check(), (i, 'no check', r)
        assert stalemate_if_taken(b), (i, 'capture not stalemate')
        cls = 'brilliant' if i in BRILLIANT else ('best' if i in BEST_ROOK else 'great')
        seq.append((RT[i], rook_sq, r, 'R', cls)); rook_sq = r
    return start_fen, seq

if __name__ == '__main__':
    fen, seq = build()
    print('start', fen)
    print(len(seq), 'half-moves OK; final:', chess.Board(fen).fen() if False else '')
    print(chess.Board(fen))
