# poker-cv-project

this is a work-in-progress as of July 13, 2025... 
Repository work is very rough drafted.

this is close to finished as of July 23, 2025... 
I have created the Streamlit deployment here: [https://ethanspokercvproject.streamlit.app/](https://poker-cv-project-bipfjg8fy7hcp9q3uebsk9.streamlit.app/)



Instructions:
1. Include a decent image of a poker board (clear and aligned is preferred) like the my picture below
2. Type in your hole cards
3. Analyze
4. (Optional - edit anything else: # of players, amount to call, etc.)

![poker-hands-royal-flush-in-texas-holdem-rankings_jpg rf b1a0bb57e20e72380e19654fd926609e](https://github.com/user-attachments/assets/8d8cc5d1-f4d6-4a78-b1e4-d31bce38114b)



My Remaining Tasks:
Cleaning up everything
Planning to make a mobile app of this as a final step.

Treys is a pure Python library designed for poker hand evaluation, and is a part of the logic used. 
The 3 files within 'originalworkincolab' are optional to view; they are cluttered and were done in Google Colab for the free GPU and training (its my raw work). 
I gathered data from Kaggle, and also gathered my own images by taking pictures of various poker boards from different angles. 
Roboflow was used for labeling (and training?). 
My 'best.pt' model is called 'fromthetrash' in cv_pipeline.py because it somehow landed in my laptop's Trash. When comparing my different 'best.pt' models, the 'fromthetrash' one had the highest accuracy of 94%, so I decided to use that.
