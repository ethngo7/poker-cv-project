# poker-cv-project

A computer vision–powered poker board analyzer that detects community cards from an uploaded photo, takes in user-input hole cards, evaluates hand strength, and suggests an action (fold/call/raise) based on game context.
Deployed via **Streamlit** and containerized with **Docker** for production readiness.
This project was created out of my interest in poker and computer vision. 

![poker-hands-royal-flush-in-texas-holdem-rankings_jpg rf b1a0bb57e20e72380e19654fd926609e](https://github.com/user-attachments/assets/8d8cc5d1-f4d6-4a78-b1e4-d31bce38114b)
---

## Project Overview

This project uses **YOLOv8** for object detection (community card recognition) and a **ResNet18 classifier** for rank/suit classification. It integrates **Treys** for hand evaluation and includes basic poker decision logic to provide recommendations.

**Key Features:**

* **Community card detection:** Trained on a custom dataset (Roboflow-labeled) using YOLOv8.
* **Card classification:** Fine-tuned ResNet18 model on individual card images (Kaggle + custom photos).
* **Poker logic:** Evaluates hand strength and recommends fold/call/raise based on pot odds, number of players, and stage of the hand.
* **Streamlit app:** Easy-to-use interface for real-time analysis.
* **Dockerized:** Production-ready container for hosting on Streamlit Cloud, AWS Elastic Beanstalk, or other cloud platforms.

---

## Tools & Technologies

* **Computer Vision & ML:**
  YOLOv8 (Ultralytics), PyTorch, TorchVision, ResNet18
* **Poker Evaluation:**
  Treys – Python-based poker hand evaluator
* **Data Handling:**
  Roboflow for labeling, Kaggle datasets for classifier training
* **Web Deployment:**
  Streamlit for frontend, Docker for containerization, AWS Elastic Beanstalk for scalable hosting
* **Supporting Libraries:**
  `torch`, `torchvision`, `ultralytics`, `pillow`, `numpy`, `ipython`

---

## Data & Model Training

<details>
<summary>Click to expand</summary>

1. **Datasets:**

   * **Community cards:** Images captured by me from multiple angles (flop, turn, river) + labeled via Roboflow.
   * **Individual cards:** Kaggle dataset with 53 classes (including Joker, later filtered out).
2. **Detection Model (YOLOv8):**

   * Model: YOLOv8n
   * Dataset: Roboflow-labeled poker boards
   * Validation: **94% mAP\@0.5**
3. **Classifier Model (ResNet18):**

   * Fine-tuned on Kaggle dataset
   * Validation: **92% accuracy**
4. **Poker Logic:**

   * Treys hand evaluation
   * Decision-making: fold/call/raise based on hand score, pot odds, number of players, and board stage.

</details>

---

## End-to-End Pipeline

The core pipeline (`run_hand_analysis` in `utils/cv_pipeline.py`):

1. Detect community cards from uploaded image (`YOLOv8`).
2. Classify cropped cards (`ResNet18`).
3. Convert detected cards to Treys format.
4. Evaluate hand strength using Treys.
5. Compute pot odds & apply decision logic.
6. Return a recommendation (fold/call/raise) + explanation.

---

## Running Locally

```bash
git clone https://github.com/ethngo7/poker-cv-project.git
cd poker-cv-project
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Deployment

* **Streamlit Cloud:** Live deployment at: \[https://ethanspokercv.streamlit.app/]
* **Docker:**

  ```bash
  docker build -t poker-cv-app .
  docker run -p 8501:8501 poker-cv-app
  ```
* **AWS Elastic Beanstalk:**
  Work in progress (production scaling setup).

---

## Repository Notes

* `utils/` – Core pipeline & poker logic.
* `models/` – Pretrained models (`best.pt` for YOLOv8, `card_classifier.pt` for ResNet18).
* `originalworkincolab/` – Raw Google Colab notebooks for training and experimentation.
* `requirements/` – Dependency lists for Streamlit & Docker deployments.

---

## Remaining Work

* Improve Streamlit UI (better visuals, inline help, more insights).
* Add **equity simulations** (Monte Carlo–based win probabilities).
* Deploy fully on **AWS (Elastic Beanstalk)**.
* Build **mobile version** for on-the-go use.
* Integrate **board texture analysis & draw detection** for more nuanced advice.

---

