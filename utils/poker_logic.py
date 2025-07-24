"""
Poker logic helpers:
  • String ↔ Treys conversion
  • Flush / straight draw detection
  • Board-texture analysis
  • DecisionConfiguration + decide_action()

Imports ONLY pure-Python + treys; no heavy CV libraries here.
"""

from collections import Counter
from dataclasses import dataclass
from treys import Card, Evaluator

# ------------------------------------------------------------
# 1. Treys-conversion helpers
# ------------------------------------------------------------
_RANK_ORDER = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,
               'T':10,'J':11,'Q':12,'K':13,'A':14}

_RANK_FROM_WORD = {
    'two':'2','three':'3','four':'4','five':'5','six':'6','seven':'7',
    'eight':'8','nine':'9','ten':'T','jack':'J','queen':'Q','king':'K','ace':'A'
}
_SUIT_FROM_WORD = {'clubs':'c','diamonds':'d','hearts':'h','spades':'s'}

def convert_to_treys_format(card_name: str) -> str:
    """
    'ten of clubs'  → 'Tc'
    'Ace of Hearts' → 'Ah'
    """
    """
    Accepts either digit ranks ('6 of hearts') or word ranks ('six of hearts')
    and returns Treys format ('6h').
    """
    card_name = card_name.lower().strip()
    parts = card_name.split(" of ")
    if len(parts) != 2:
        raise ValueError(f"Invalid card name format. Please write like so (e.g. six of clubs, queen of spades): {card_name}")

    rank_raw, suit_raw = parts
    rank_raw = rank_raw.strip()
    suit_raw = suit_raw.strip()

    # Map rank
    if rank_raw in _RANK_FROM_WORD:          # word: 'six'
        rank_char = _RANK_FROM_WORD[rank_raw]
    elif rank_raw in '23456789':              # digit: '6'
        rank_char = rank_raw
    elif rank_raw == '10':
        rank_char = 'T'
    else:
        raise ValueError(f"Unknown rank '{rank_raw}' in: {card_name}")

    # Map suit
    try:
        suit_char = _SUIT_FROM_WORD[suit_raw]
    except KeyError:
        raise ValueError(f"Unknown suit '{suit_raw}' in: {card_name}")

    return rank_char + suit_char


def _rank_val(card:str) -> int:
    return _RANK_ORDER[card[0].upper()]

def _suit_char(card:str) -> str:
    return card[-1].lower()

# ------------------------------------------------------------
# 2. Flush & straight draw helpers
# ------------------------------------------------------------
def has_flush_draw(hole, board, need=4):
    suits = [_suit_char(c) for c in hole+board]
    return any(v >= need for v in Counter(suits).values())

def made_flush(hole, board):
    return has_flush_draw(hole, board, need=5)

def _unique_sorted_ranks_with_wheel(cards):
    ranks = {_rank_val(c) for c in cards}
    if 14 in ranks: 
        ranks.add(1)  # Ace low
    return sorted(ranks)

def has_straight_draw(hole, board):
    cards = hole+board
    ranks = _unique_sorted_ranks_with_wheel(cards)
    if len(ranks) < 4:
        return {'open_ended':False,'gutshot':False,'made_straight':False,'any_draw':False}

    open_ended = gutshot = made = False
    rset = set(ranks)
    for low in range(1,11):
        want = {low+i for i in range(5)}
        have = want & rset
        miss = 5 - len(have)
        if miss == 0:
            made = True
        elif miss == 1:
            sorted_have = sorted(have)
            if max(have) - min(have) == 4:
                gutshot = True
            else:
                consec = sorted_have[-1]-sorted_have[0]==3 and len(sorted_have)==4
                if consec: 
                    open_ended = True
                else: 
                    gutshot = True
    return {'open_ended':open_ended,'gutshot':gutshot,
            'made_straight':made,'any_draw':made or open_ended or gutshot}

# ------------------------------------------------------------
# 3. Board texture
# ------------------------------------------------------------
@dataclass
class BoardTexture:
    stage:str; paired:bool; trips_or_better:bool
    monotone:bool; two_tone:bool; rainbow:bool
    straighty:bool; high_card:int; low_card:int; ranks:list

def get_game_stage(board):
    n=len(board)
    return {3:'flop',4:'turn',5:'river'}.get(n,'pre-flop')

def analyze_board_texture(board):
    stage=get_game_stage(board)
    suits=[_suit_char(c) for c in board]
    suit_cnt=Counter(suits)
    monotone=len(suit_cnt)==1
    two_tone=len(suit_cnt)==2
    rainbow=len(suit_cnt)>=3
    ranks=sorted((_rank_val(c) for c in board),reverse=True)
    rank_cnt=Counter(ranks)
    paired=any(v>=2 for v in rank_cnt.values())
    trips_or_better=any(v>=3 for v in rank_cnt.values())
    uniq=_unique_sorted_ranks_with_wheel(board)
    straighty=len(uniq)>=3 and max(uniq)-min(uniq)<=4
    return BoardTexture(stage,paired,trips_or_better,monotone,two_tone,rainbow,
                        straighty,max(ranks) if ranks else None,
                        min(ranks) if ranks else None,ranks)

# ------------------------------------------------------------
# 4. Decision engine
# ------------------------------------------------------------
@dataclass
class DecisionConfiguration:
    max_players:int=10
    base_raise_score:int=3500
    base_call_score:int=5000
    player_tighten_strength:float=0.5
    stage_mult:dict=None
    pot_odds_raise_cap:float=0.35
    pot_odds_call_cap:float=0.70
    draw_loosen_mult:float=0.85
    monster_loosen_mult:float=0.7
    texture_tighten_mult:float=1.15
    def __post_init__(self):
        if self.stage_mult is None:
            self.stage_mult={'pre-flop':1.3,'flop':1.2,'turn':1.0,'river':0.8}

def decide_action(hand_score:int,num_players:int,hole,board,pot_odds:float,
                  cfg:DecisionConfiguration=DecisionConfiguration(),
                  return_explanation=False):
    # Stage & player factor
    stage=get_game_stage(board)
    stage_factor=cfg.stage_mult.get(stage,1.0)
    num_players=max(2,min(num_players,cfg.max_players))
    frac=(num_players-2)/(cfg.max_players-2) if cfg.max_players>2 else 0.0
    player_factor=1.0+cfg.player_tighten_strength*frac
    adjusted=hand_score*stage_factor*player_factor

    # Draws & board texture
    fd = has_flush_draw(hole,board,4)
    made_f = made_flush(hole,board)
    sd = has_straight_draw(hole,board)
    made_s = sd['made_straight']
    bt = analyze_board_texture(board)

    if made_f or made_s:
        adjusted*=cfg.monster_loosen_mult
    if stage in ('flop','turn') and (fd or sd['any_draw']) and pot_odds<=cfg.pot_odds_call_cap:
        adjusted*=cfg.draw_loosen_mult

    # tighten for scary board we don't hit
    tighten=False
    if bt.paired:
        if {_rank_val(c) for c in hole}.isdisjoint({_rank_val(c) for c in board}):
            tighten=True
    if bt.monotone and not tighten:
        b_suit={_suit_char(c) for c in board}
        if not any(_suit_char(c) in b_suit for c in hole):
            tighten=True
    if bt.straighty and not tighten:
        hv=sorted({_rank_val(c) for c in hole})
        br=sorted({_rank_val(c) for c in board})
        if hv and (hv[-1]<br[0]-1 and hv[0]>br[-1]+1):
            tighten=True
    if tighten:
        adjusted*=cfg.texture_tighten_mult

    exp_call  = pot_odds>=cfg.pot_odds_call_cap
    exp_raise = pot_odds>=cfg.pot_odds_raise_cap
    monster   = adjusted<0.5*cfg.base_raise_score

    if adjusted<cfg.base_raise_score and not exp_raise:
        action='raise'
    elif adjusted<cfg.base_raise_score and exp_raise and monster:
        action='raise'
    elif adjusted<cfg.base_call_score and not exp_call:
        action='call'
    elif adjusted<cfg.base_call_score and exp_call and monster:
        action='call'
    else:
        action='fold'

    if return_explanation:
        return action, dict(stage=stage,player_factor=player_factor,
                            stage_factor=stage_factor,flush_draw=fd,
                            straight_info=sd,board_texture=bt,
                            adjusted_score=adjusted,action=action)
    return action
