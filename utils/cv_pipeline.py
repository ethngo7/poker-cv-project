"""
Computer-vision + poker pipeline:
  • YOLOv8 detects community cards
  • ResNet classifier identifies rank+suit
  • run_hand_analysis() ties everything together
"""

import os, torch, numpy as np
from pathlib import Path
from PIL import Image
from ultralytics import YOLO
from torchvision import datasets, models, transforms
from IPython import display

from utils.poker_logic import (convert_to_treys_format, decide_action,
                               DecisionConfiguration)
from treys import Card, Evaluator

# ------------------------------------------------------------
# 1. Load models once (global singletons)
# ------------------------------------------------------------

DETECTOR = YOLO("models/fromthetrash_best.pt") # mAP50: 0.974
# DETECTOR = YOLO("models/best.pt") # mAP50: 0.946
# DETECTOR = YOLO("runs/runs2/detect/train/weights/best.pt") # mAP50: 0.974

_CLASSIFIER = models.resnet18()
_CLASSIFIER.fc = torch.nn.Linear(_CLASSIFIER.fc.in_features, 53)
_CLASSIFIER.load_state_dict(torch.load("models/card_classifier.pt",
                                      map_location="cpu"))
_CLASSIFIER.eval()

_TFM = transforms.Compose([
    transforms.Resize(128),
    transforms.CenterCrop(128),
    transforms.ToTensor()
])

'''_CLASS_LABELS = datasets.ImageFolder(
    "data/kaggle_individual_cards/train"
).classes'''

_CLASS_LABELS = [
    'ace of clubs', 'ace of diamonds', 'ace of hearts', 'ace of spades',
    'eight of clubs', 'eight of diamonds', 'eight of hearts', 'eight of spades',
    'five of clubs', 'five of diamonds', 'five of hearts', 'five of spades',
    'four of clubs', 'four of diamonds', 'four of hearts', 'four of spades',
    'jack of clubs', 'jack of diamonds', 'jack of hearts', 'jack of spades',
    'joker',
    'king of clubs', 'king of diamonds', 'king of hearts', 'king of spades',
    'nine of clubs', 'nine of diamonds', 'nine of hearts', 'nine of spades',
    'queen of clubs', 'queen of diamonds', 'queen of hearts', 'queen of spades',
    'seven of clubs', 'seven of diamonds', 'seven of hearts', 'seven of spades',
    'six of clubs', 'six of diamonds', 'six of hearts', 'six of spades',
    'ten of clubs', 'ten of diamonds', 'ten of hearts', 'ten of spades',
    'three of clubs', 'three of diamonds', 'three of hearts', 'three of spades',
    'two of clubs', 'two of diamonds', 'two of hearts', 'two of spades'
]


# ------------------------------------------------------------
# 2. Card detection + classification
# ------------------------------------------------------------
def predict_cards(image_path:str, show=False):
    """
    Runs YOLOv8 community-card detector and ResNet classifier.
    Returns list of human-readable labels e.g. ['ten of hearts', ...]
    """
    results = DETECTOR(image_path, save = True, conf=0.7)
    boxes = results[0].boxes.xyxy.cpu().numpy()
    confs = results[0].boxes.conf.cpu().numpy()
    H = results[0].orig_shape[0]

    # Sort boxes by confidence
    order = confs.argsort()[::-1]
    boxes = boxes[order]
    confs = confs[order]
    #row_tol = 0.12*H
    row_tol = 0.05*H
    kept=[]
    base_y=None
    for b in boxes:
        x1,y1,x2,y2=b 
        yc=(y1+y2)/2
        if base_y is None or abs(yc-base_y)<row_tol:
            base_y = yc if base_y is None else base_y
            kept.append([int(x1), int(y1), int(x2), int(y2)])
        if len(kept)==5: 
            break

    # classify
    img = Image.open(image_path).convert("RGB")
    card_preds = []
    for x1, y1, x2, y2 in kept:
        crop = img.crop((x1, y1, x2, y2))
        tensor = _TFM(crop).unsqueeze(0)          # 128-resize → tensor
        with torch.no_grad():
            out = _CLASSIFIER(tensor)
            idx = out.argmax(dim=1).item()
            label = _CLASS_LABELS[idx]
            if label != "joker":                  # ignore jokers
                card_preds.append(label)

    if show:
        display(img.resize((400, None)))
        print("Detected:", card_preds)

    return card_preds

# ------------------------------------------------------------
# 3. End-to-end wrapper
# ------------------------------------------------------------
def run_hand_analysis(image_path:str,
                      hole_input:str,
                      num_players:int,
                      call_amt:float,
                      pot_before:float,
                      cfg:DecisionConfiguration=DecisionConfiguration()):
    """
    Full pipeline → returns dict summarising everything.
    """
    # Detect + classify boards
    board_human = predict_cards(image_path)
    board_human = [c for c in board_human if c != "joker"]
    board_treys = [convert_to_treys_format(c) for c in board_human]

    # Parse hole input
    hole_human = [c.strip().lower() for c in hole_input.replace(" and ",",").split(",")]
    hole_treys = [convert_to_treys_format(c) for c in hole_human]

    # Validation to prevent Treys from crashing (Treys checks 5-7 cards)
    if len(board_treys) < 3:
        raise ValueError(f"Only detected {len(board_treys)} community cards "
                         "(need at least 3 for flop).")
    if len(hole_treys) != 2:
        raise ValueError("Hole-card input must contain exactly two cards "
                         "like 'ten of clubs, ace of diamonds'.")
    # Treys evaluation
    evaluator=Evaluator()
    score = evaluator.evaluate([Card.new(c) for c in board_treys],
                               [Card.new(c) for c in hole_treys])

    pot_odds = call_amt/(pot_before+call_amt) if (pot_before+call_amt) else 0.0

    action, expl = decide_action(score, num_players, hole_treys, board_treys,
                                 pot_odds, cfg, return_explanation=True)

    return dict(
        community_human  = board_human,
        community_treys  = board_treys,
        hole_human       = hole_human,
        hole_treys       = hole_treys,
        hand_score       = score,
        stage            = expl['stage'],
        pot_odds         = pot_odds,
        action           = action,
        explain          = expl
    )
