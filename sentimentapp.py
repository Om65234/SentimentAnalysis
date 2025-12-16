import speech_recognition as sr  # Import speech recognition library
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import ttk, messagebox
import ttkbootstrap
from azure.core.credentials import AzureKeyCredential
from azure.ai.textanalytics import TextAnalyticsClient

# --- Your Azure Credentials ---
AZURE_API_KEY = os.getenv("AZURE_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")

# --- Authentication ---
try:
    credential = AzureKeyCredential(AZURE_API_KEY)
    text_analytics_client = TextAnalyticsClient(endpoint=AZURE_ENDPOINT, credential=credential)
except Exception as e:
    messagebox.showerror("Authentication Error", f"Could not connect to Azure. Please check your API Key and Endpoint.\nError: {e}")
    exit()

# --- Microphone Input Functionality ---
recording = False  # Global variable to track recording state

def toggle_microphone():
    """Toggles the microphone recording state."""
    global recording
    if not recording:
        start_recording()
    else:
        stop_recording()

def start_recording():
    """Starts recording voice input."""
    global recording
    recording = True
    microphone_button.configure(text="🔴 Recording")  # Change button text to indicate recording
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        messagebox.showinfo("Voice Input", "Please speak now...")
        try:
            audio = recognizer.listen(source, timeout=10)  # Listen for voice input
            text = recognizer.recognize_google(audio)  # Convert audio to text using Google API
            text_entry.delete("1.0", "end")  # Clear existing text
            text_entry.insert("1.0", text)  # Insert the recognized text into the text box
        except sr.UnknownValueError:
            messagebox.showerror("Voice Input Error", "Sorry, could not understand your voice.")
        except sr.RequestError:
            messagebox.showerror("Voice Input Error", "Could not request results from the speech recognition service.")
        except Exception as e:
            messagebox.showerror("Voice Input Error", f"An error occurred: {e}")
    stop_recording()  # Automatically stop recording after processing

def stop_recording():
    """Stops recording voice input."""
    global recording
    recording = False
    microphone_button.configure(text="🎤 Speak")  # Reset button text to default

# --- Main Analysis Function ---
def run_all_analyses():
    """Runs sentiment analysis and populates the Opinion Mining tab."""
    input_text = text_entry.get("1.0", "end-1c").strip()
    if not input_text:
        messagebox.showwarning("Input Error", "Please enter some text to analyze.")
        return
    
    documents = [input_text]

    try:
        # --- Sentiment Analysis ---
        sentiment_response = text_analytics_client.analyze_sentiment(documents=documents, show_opinion_mining=True)[0]
        if not sentiment_response.is_error:
            positive_score = sentiment_response.confidence_scores.positive
            neutral_score = sentiment_response.confidence_scores.neutral
            negative_score = sentiment_response.confidence_scores.negative

            positive_score_label.configure(text=f"{positive_score:.1%}")
            neutral_score_label.configure(text=f"{neutral_score:.1%}")
            negative_score_label.configure(text=f"{negative_score:.1%}")

            positive_progress.set(positive_score)
            neutral_progress.set(neutral_score)
            negative_progress.set(negative_score)

            # --- Determine and Display Overall Sentiment Summary ---
            summary_text = ""
            text_color = "white"
            
            # Define a threshold for "Mixed" sentiment
            MIXED_THRESHOLD = 0.20 

            if positive_score > negative_score and positive_score > neutral_score:
                summary_text = "The overall sentiment appears to be Positive."
                text_color = "#28A745" # Green
            elif negative_score > positive_score and negative_score > neutral_score:
                summary_text = "The overall sentiment appears to be Negative."
                text_color = "#DC3545" # Red
            elif neutral_score > positive_score and neutral_score > negative_score:
                summary_text = "The overall sentiment appears to be Neutral."
                text_color = "#17A2B8" # Blue
            # If positive and negative are close, it's mixed
            elif abs(positive_score - negative_score) < MIXED_THRESHOLD:
                summary_text = "The overall sentiment appears to be Mixed."
                text_color = "#FFC107" # Yellow/Amber
            else: # Fallback for other edge cases
                summary_text = "Sentiment analysis complete."
                text_color = "gray70"
                
            summary_label.configure(text=summary_text, text_color=text_color)

            # --- Populate Opinion Mining Tab ---
            for widget in opinion_mining_frame.winfo_children():
                widget.destroy()  # Clear previous results


            sentence_counter = 1  # Counter for numbering sentences
            for sentence in sentiment_response.sentences:
                # Display the sentence text with numbering
                sentence_label = ctk.CTkLabel(
                    opinion_mining_frame,
                    text=f"{sentence_counter}) Sentence:\n{sentence.text}",
                    font=("Arial", 20, "bold"),  # Increased font size
                    justify="left",
                    text_color="white"
                )
                sentence_label.pack(anchor="w", padx=10, pady=(10, 5))

                # Display confidence scores for the sentence
                scores_text = (
                    f"Positive: {sentence.confidence_scores.positive:.1%} | "
                    f"Neutral: {sentence.confidence_scores.neutral:.1%} | "
                    f"Negative: {sentence.confidence_scores.negative:.1%}"
                )
                scores_label = ctk.CTkLabel(
                    opinion_mining_frame,
                    text=scores_text,
                    font=("Arial", 18),  # Increased font size
                    justify="left",
                    text_color="#A9A9A9"  # Light gray for secondary information
                )
                scores_label.pack(anchor="w", padx=20, pady=(0, 10))

                # Display mined opinions with proper formatting
                opinion_counter = 1  # Counter for numbering opinions within a sentence
                for opinion in sentence.mined_opinions:
                    target_label = ctk.CTkLabel(
                        opinion_mining_frame,
                        text=f"  {opinion_counter}) Target: {opinion.target.text} ({opinion.target.sentiment.capitalize()})",
                        font=("Arial", 18, "bold"),  # Increased font size
                        justify="left",
                        text_color="#FFD700"  # Gold for emphasis
                    )
                    target_label.pack(anchor="w", padx=30, pady=(5, 5))

                    for assessment in opinion.assessments:
                        assessment_label = ctk.CTkLabel(
                            opinion_mining_frame,
                            text=f"    - {assessment.text} ({assessment.sentiment.capitalize()})",
                            font=("Arial", 16),  # Increased font size
                            justify="left",
                            text_color="white"
                        )
                        assessment_label.pack(anchor="w", padx=50, pady=(2, 2))
        
                    opinion_counter += 1  # Increment opinion counter

                sentence_counter += 1  # Increment sentence counter

    except Exception as e:
        messagebox.showerror("Runtime Error", f"An error occurred during analysis: {e}")

# --- GUI Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Sentiment Analysis Dashboard")
app.geometry("1200x800")

# --- Layout Configuration ---
app.grid_columnconfigure(0, weight=1)
app.grid_rowconfigure(1, weight=1)

# --- Input Frame (Stays at the top) ---
input_frame = ctk.CTkFrame(app, fg_color="transparent")
input_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
input_frame.grid_columnconfigure(0, weight=1)

# Create a scrollable text entry box
text_entry = ctk.CTkTextbox(input_frame, height=250, font=("Arial", 20), wrap="word")
text_entry.grid(row=0, column=0, sticky="nsew")

# Add vertical scrollbar for the text entry box
text_entry_scrollbar = ctk.CTkScrollbar(input_frame, orientation="vertical", command=text_entry.yview)
text_entry_scrollbar.grid(row=0, column=1, sticky="ns")

# Configure the scrollbar to work with the text entry box
text_entry.configure(yscrollcommand=text_entry_scrollbar.set)

# Add a microphone button for voice input
microphone_button = ctk.CTkButton(input_frame, text="🎤 Speak", command=toggle_microphone, height=60, font=("Arial", 20, "bold"))
microphone_button.grid(row=0, column=2, padx=20, sticky="ns")

# Increase the size of the Analyze button
analyze_button = ctk.CTkButton(input_frame, text="Analyze", command=run_all_analyses, height=60, font=("Arial", 20, "bold"))
analyze_button.grid(row=0, column=3, padx=20, sticky="ns")

# --- Tab View ---
tab_view = ctk.CTkTabview(app, corner_radius=10, border_width=2)
tab_view.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")

sentiment_tab = tab_view.add("Sentiment Analysis")

# Add Opinion Mining Tab
opinion_mining_tab = tab_view.add("Opinion Mining")

# Create a canvas for the opinion mining frame with scrollbars
opinion_mining_canvas = ctk.CTkCanvas(opinion_mining_tab, width=1200, height=600, bg="#1C1C1C", highlightthickness=0)
opinion_mining_canvas.grid(row=0, column=0, sticky="nsew")

# Add vertical scrollbar for the opinion mining frame
opinion_mining_vertical_scrollbar = ctk.CTkScrollbar(opinion_mining_tab, orientation="vertical", command=opinion_mining_canvas.yview)
opinion_mining_vertical_scrollbar.grid(row=0, column=1, sticky="ns")

# Add horizontal scrollbar for the opinion mining frame
opinion_mining_horizontal_scrollbar = ctk.CTkScrollbar(opinion_mining_tab, orientation="horizontal", command=opinion_mining_canvas.xview)
opinion_mining_horizontal_scrollbar.grid(row=1, column=0, sticky="ew")

# Configure canvas scroll region
opinion_mining_canvas.configure(yscrollcommand=opinion_mining_vertical_scrollbar.set, xscrollcommand=opinion_mining_horizontal_scrollbar.set)

# Create a scrollable frame inside the canvas
opinion_mining_frame = ctk.CTkFrame(opinion_mining_canvas, fg_color="transparent")
opinion_mining_canvas.create_window((0, 0), window=opinion_mining_frame, anchor="nw")

# Bind resizing events to update the scroll region
def update_opinion_mining_scroll_region(event):
    opinion_mining_canvas.configure(scrollregion=opinion_mining_canvas.bbox("all"))

opinion_mining_frame.bind("<Configure>", update_opinion_mining_scroll_region)

# Ensure the tab expands properly
opinion_mining_tab.grid_columnconfigure(0, weight=1)
opinion_mining_tab.grid_rowconfigure(0, weight=1)

# --- Configure Grids for each Tab to allow expansion ---
sentiment_tab.grid_columnconfigure(0, weight=1)

# ============================================
# TAB 1: SENTIMENT ANALYSIS UI
# ============================================
cards_frame = ctk.CTkFrame(sentiment_tab, fg_color="transparent")
cards_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

# Positive Card
positive_card = ctk.CTkFrame(cards_frame, fg_color="#1F2A24", corner_radius=10)
positive_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
ctk.CTkLabel(positive_card, text="Positive 😀", font=("Segoe UI Emoji", 22)).pack(pady=(10, 5))
positive_score_label = ctk.CTkLabel(positive_card, text="0.0%", font=("Arial", 28, "bold"))
positive_score_label.pack()
positive_progress = ctk.CTkProgressBar(positive_card, progress_color="#28A745", fg_color="#333333")
positive_progress.set(0)
positive_progress.pack(pady=(5, 15), padx=20, fill="x")

# Neutral Card
neutral_card = ctk.CTkFrame(cards_frame, fg_color="#1F2733", corner_radius=10)
neutral_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
ctk.CTkLabel(neutral_card, text="Neutral 😐", font=("Segoe UI Emoji", 22)).pack(pady=(10, 5))
neutral_score_label = ctk.CTkLabel(neutral_card, text="0.0%", font=("Arial", 28, "bold"))
neutral_score_label.pack()
neutral_progress = ctk.CTkProgressBar(neutral_card, progress_color="#17A2B8", fg_color="#333333")
neutral_progress.set(0)
neutral_progress.pack(pady=(5, 15), padx=20, fill="x")

# Negative Card
negative_card = ctk.CTkFrame(cards_frame, fg_color="#2E2024", corner_radius=10)
negative_card.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
ctk.CTkLabel(negative_card, text="Negative 😡", font=("Segoe UI Emoji", 22)).pack(pady=(10, 5))
negative_score_label = ctk.CTkLabel(negative_card, text="0.0%", font=("Arial", 28, "bold"))
negative_score_label.pack()
negative_progress = ctk.CTkProgressBar(negative_card, progress_color="#DC3545", fg_color="#333333")
negative_progress.set(0)
negative_progress.pack(pady=(5, 15), padx=20, fill="x")

# --- Overall Analysis Frame ---
summary_frame = ctk.CTkFrame(sentiment_tab, fg_color="#1C1C1C", corner_radius=10)
summary_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

summary_label = ctk.CTkLabel(summary_frame, text="Analysis summary will appear here.", font=("Arial", 16, "italic"), text_color="gray60")
summary_label.pack(padx=10, pady=10)

# --- Run App ---
app.mainloop()