import logging
import streamlit as st
import json
import uuid
import zipfile
import io
import re
from pathlib import Path

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Function to generate a unique UUID
def generate_uuid():
    return str(uuid.uuid4())

# Function to map MultipleChoice questions to H5P format
def map_multiple_choice(question):
    try:
        h5p_question = {
            "library": "H5P.MultiChoice 1.16",
            "params": {
                "question": question.get("question", "Keine Frage gestellt."),
                "answers": [],
                "behaviour": {
                    "singleAnswer": True,
                    "enableRetry": False,
                    "enableSolutionsButton": False,
                    "enableCheckButton": True,
                    "type": "auto",
                    "singlePoint": False,
                    "randomAnswers": True,  # This will be controlled globally
                    "showSolutionsRequiresInput": True,
                    "confirmCheckDialog": False,
                    "confirmRetryDialog": False,
                    "autoCheck": False,
                    "passPercentage": 100,
                    "showScorePoints": True
                },
                "media": {
                    "disableImageZooming": False
                },
                "overallFeedback": [
                    {
                        "from": 0,
                        "to": 100
                    }
                ],
                "UI": {
                    "checkAnswerButton": "Überprüfen",
                    "submitAnswerButton": "Absenden",
                    "showSolutionButton": "Lösung anzeigen",
                    "tryAgainButton": "Wiederholen",
                    "tipsLabel": "Hinweis anzeigen",
                    "scoreBarLabel": "Du hast :num von :total Punkten erreicht.",
                    "tipAvailable": "Hinweis verfügbar",
                    "feedbackAvailable": "Rückmeldung verfügbar",
                    "readFeedback": "Rückmeldung vorlesen",
                    "wrongAnswer": "Falsche Antwort",
                    "correctAnswer": "Richtige Antwort",
                    "shouldCheck": "Hätte gewählt werden müssen",
                    "shouldNotCheck": "Hätte nicht gewählt werden sollen",
                    "noInput": "Bitte antworte, bevor du die Lösung ansiehst",
                    "a11yCheck": "Die Antworten überprüfen. Die Auswahlen werden als richtig, falsch oder fehlend markiert.",
                    "a11yShowSolution": "Die Lösung anzeigen. Die richtigen Lösungen werden in der Aufgabe angezeigt.",
                    "a11yRetry": "Die Aufgabe wiederholen. Alle Versuche werden zurückgesetzt und die Aufgabe wird erneut gestartet."
                },
                "confirmCheck": {
                    "header": "Beenden?",
                    "body": "Ganz sicher beenden?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Beenden"
                },
                "confirmRetry": {
                    "header": "Wiederholen?",
                    "body": "Ganz sicher wiederholen?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Bestätigen"
                }
            },
            "subContentId": generate_uuid(),
            "metadata": {
                "contentType": "Multiple Choice",
                "license": "U",
                "title": "Multiple Choice",
                "authors": [],
                "changes": [],
                "extraTitle": "Multiple Choice"
            }
        }

        options = question.get("options", [])
        if not isinstance(options, list):
            st.warning(f"'options' is not a list in MultipleChoice question: {question.get('question', 'Keine Frage')}")
            return h5p_question

        for option in options:
            answer = {
                "text": option.get("text", ""),
                "correct": option.get("is_correct", False),
                "tipsAndFeedback": {
                    "tip": "",
                    "chosenFeedback": f"<div>{option.get('feedback', '')}</div>\n",
                    "notChosenFeedback": ""
                }
            }
            h5p_question["params"]["answers"].append(answer)

        return h5p_question

    except Exception as e:
        st.error(f"Error mapping MultipleChoice question: {e}")
        return {}

# Function to map TrueFalse questions to H5P format
def map_true_false(question):
    try:
        correct_answer = question.get("correct_answer", False)
        feedback_correct = question.get("feedback_correct", "")
        feedback_incorrect = question.get("feedback_incorrect", "")

        h5p_question = {
            "library": "H5P.TrueFalse 1.8",
            "params": {
                "question": question.get("question", "Keine Frage gestellt."),
                "correct": "true" if correct_answer else "false",
                "behaviour": {
                    "enableRetry": False,
                    "enableSolutionsButton": False,
                    "enableCheckButton": True,
                    "confirmCheckDialog": False,
                    "confirmRetryDialog": False,
                    "autoCheck": False,
                    "feedbackOnCorrect": feedback_correct,
                    "feedbackOnWrong": feedback_incorrect
                },
                "media": {
                    "disableImageZooming": False
                },
                "l10n": {
                    "trueText": "Wahr",
                    "falseText": "Falsch",
                    "score": "Du hast @score von @total Punkten erreicht.",
                    "checkAnswer": "Überprüfen",
                    "submitAnswer": "Absenden",
                    "showSolutionButton": "Lösung anzeigen",
                    "tryAgain": "Wiederholen",
                    "wrongAnswerMessage": "Falsche Antwort",
                    "correctAnswerMessage": "Richtige Antwort",
                    "scoreBarLabel": "Du hast :num von :total Punkten erreicht.",
                    "a11yCheck": "Die Antworten überprüfen. Die Antwort wird als richtig, falsch oder unbeantwortet markiert.",
                    "a11yShowSolution": "Die Lösung anzeigen. Die richtige Lösung wird in der Aufgabe angezeigt.",
                    "a11yRetry": "Die Aufgabe wiederholen. Alle Versuche werden zurückgesetzt, und die Aufgabe wird erneut gestartet."
                },
                "confirmCheck": {
                    "header": "Beenden?",
                    "body": "Ganz sicher beenden?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Beenden"
                },
                "confirmRetry": {
                    "header": "Wiederholen?",
                    "body": "Ganz sicher wiederholen?",
                    "cancelLabel": "Abbrechen",
                    "confirmLabel": "Bestätigen"
                }
            },
            "subContentId": generate_uuid(),
            "metadata": {
                "contentType": "True/False Question",
                "license": "U",
                "title": "Richtig Falsch",
                "authors": [],
                "changes": [],
                "extraTitle": "Richtig Falsch"
            }
        }

        return h5p_question

    except Exception as e:
        st.error(f"Error mapping TrueFalse question: {e}")
        return {}


def create_full_content_structure(questions, youtube_url, title, randomization, pool_size, pass_percentage):
    """Create the complete content structure with text, video, and questions"""
    try:
        # Extract YouTube ID if URL is provided
        youtube_id = None
        if youtube_url:
            match = re.search(r"v=([a-zA-Z0-9_-]{11})", youtube_url)
            if match:
                youtube_id = match.group(1)
        
        return {
            "content": [
                # Text Section
                {
                    "content": {
                        "params": {
                            "text": "<p>Schauen Sie das Video und beantworten Sie die Verständnisfragen unterhalb des Videos</p>"
                        },
                        "library": "H5P.AdvancedText 1.1",
                        "metadata": {
                            "contentType": "Text",
                            "license": "U",
                            "title": "Intro Text",
                            "authors": [],
                            "changes": []
                        },
                        "subContentId": generate_uuid()
                    },
                    "useSeparator": "auto"
                },
                # Video Section
                {
                    "content": {
                        "params": {
                            "visuals": {"fit": True, "controls": True},
                            "playback": {"autoplay": False, "loop": False},
                            "l10n": {
                                "name": "Video",
                                "loading": "Videoplayer lädt...",
                                # ... (keep all l10n properties from example)
                            },
                            "sources": [{
                                "path": f"https://www.youtube.com/watch?v={youtube_id}" if youtube_id else "",
                                "mime": "video/YouTube",
                                "copyright": {"license": "U"},
                                "aspectRatio": "16:9"
                            }]
                        },
                        "library": "H5P.Video 1.6",
                        "metadata": {
                            "contentType": "Video",
                            "license": "U",
                            "title": "YouTube Video",
                            "authors": [],
                            "changes": [],
                            "extraTitle": "YouTube Video"
                        },
                        "subContentId": generate_uuid()
                    },
                    "useSeparator": "auto"
                },
                # Question Set
                {
                    "useSeparator": "auto",
                    "content": {
                        "library": "H5P.QuestionSet 1.20",
                        "params": {
                            "introPage": {
                                "showIntroPage": True,
                                "startButtonText": "Quiz starten",
                                "title": title,
                                "introduction": f"<p style='text-align:center'><strong>Starten Sie das Quiz zu diesem Videoinhalt.</strong></p><p style='text-align:center'>Es werden zufällig {pool_size} Fragen angezeigt.</p>",
                                "backgroundImage": {
                                    "path": "images/file-_jmSDW4b9EawjImv.png",
                                    "mime": "image/png",
                                    "copyright": {"license": "U"},
                                    "width": 52,
                                    "height": 52
                                }
                            },
                            "progressType": "textual",
                            "passPercentage": pass_percentage,
                            "randomQuestions": randomization,
                            "poolSize": pool_size,
                            "questions": questions,
                            # ... (keep other params from example)
                        },
                        "metadata": {
                            "contentType": "Question Set",
                            "license": "U",
                            "title": title,
                            "authors": [],
                            "changes": []
                        },
                        "subContentId": generate_uuid()
                    }
                }
            ]
        }
    except Exception as e:
        st.error(f"Error creating content structure: {e}")
        return None

# Modified processing function
def process_input(youtube_url, json_data, template_path, title, randomization, pool_size, pass_percentage, user_image=None):
    try:
        # Map questions
        questions = []
        for q in json_data.get("questions", []):
            if q["type"] == "MultipleChoice":
                questions.append(map_multiple_choice(q))
            elif q["type"] == "TrueFalse":
                questions.append(map_true_false(q))
        
        # Create full content structure
        content = create_full_content_structure(
            questions=questions,
            youtube_url=youtube_url,
            title=title,
            randomization=randomization,
            pool_size=pool_size,
            pass_percentage=pass_percentage
        )
        
        # Create in-memory H5P package
        return create_h5p_package(
            content_json=json.dumps(content, ensure_ascii=False),
            template_zip_path=template_path,
            title=title,
            user_image_bytes=user_image
        )
    except Exception as e:
        st.error(f"Processing error: {e}")
        return None

# Modified H5P package creation
def create_h5p_package(content_json, template_zip_path, title, user_image_bytes=None):
    try:
        with open(template_zip_path, "rb") as f:
            template = io.BytesIO(f.read())
        
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(template, "r") as zin, zipfile.ZipFile(mem_zip, "w") as zout:
            # Copy existing files
            for item in zin.infolist():
                zout.writestr(item, zin.read(item.filename))
            
            # Add content.json
            zout.writestr("content/content.json", content_json.encode("utf-8"))
            
            # Add image if provided
            if user_image_bytes:
                zout.writestr("content/images/file-_jmSDW4b9EawjImv.png", user_image_bytes)

            # Create and add h5p.json with dynamic titles
            h5p_content = {
                "embedTypes": ["iframe"],
                "language": "en",
                "defaultLanguage": "de",
                "license": "U",
                "extraTitle": title,
                "title": title,
                "mainLibrary": "H5P.Column",
                "preloadedDependencies": [
                    {"machineName": "H5P.AdvancedText", "majorVersion": 1, "minorVersion": 1},
                    {"machineName": "H5P.Video", "majorVersion": 1, "minorVersion": 6},
                    {"machineName": "H5P.QuestionSet", "majorVersion": 1, "minorVersion": 20},
                    {"machineName": "FontAwesome", "majorVersion": 4, "minorVersion": 5},
                    {"machineName": "H5P.JoubelUI", "majorVersion": 1, "minorVersion": 3},
                    {"machineName": "H5P.Transition", "majorVersion": 1, "minorVersion": 0},
                    {"machineName": "H5P.FontIcons", "majorVersion": 1, "minorVersion": 0},
                    {"machineName": "H5P.MultiChoice", "majorVersion": 1, "minorVersion": 16},
                    {"machineName": "H5P.Question", "majorVersion": 1, "minorVersion": 5},
                    {"machineName": "H5P.TrueFalse", "majorVersion": 1, "minorVersion": 8},
                    {"machineName": "H5P.Column", "majorVersion": 1, "minorVersion": 18}
                ]
            }
            
            h5p_json_str = json.dumps(h5p_content, indent=4)
            zout.writestr("h5p.json", h5p_json_str.encode("utf-8"))
        
        mem_zip.seek(0)
        return mem_zip.getvalue()
    except Exception as e:
        st.error(f"Package creation failed: {e}")
        return None

# Streamlit UI
def main():
    st.title("Video Quiz H5P Generator")
    
    # Inputs
    youtube_url = st.text_input("YouTube Video URL")
    questions_json = st.text_area("Paste Question JSON", height=300)
    title = st.text_input("Quiz Title", "Video Quiz")
    
    # Options
    with st.sidebar:
        st.header("Settings")
        randomization = st.checkbox("Randomize Questions", True)
        pool_size = st.slider("Questions per Round", 1, 20, 7)
        pass_percentage = st.slider("Passing Percentage", 50, 100, 75)
        user_image = st.file_uploader("Title Image", type=["png", "jpg"])
    
    if st.button("Generate H5P"):
        if questions_json:
            try:
                json_data = json.loads(questions_json)
                image_bytes = user_image.read() if user_image else None
                
                h5p_package = process_input(
                    youtube_url=youtube_url,
                    json_data=json_data,
                    template_path=Path(__file__).parent / "templates" / "col_vid_mc_tf.zip",
                    title=title,
                    randomization=randomization,
                    pool_size=pool_size,
                    pass_percentage=pass_percentage,
                    user_image=image_bytes
                )
                
                if h5p_package:
                    st.download_button(
                        label="Download H5P",
                        data=h5p_package,
                        file_name="video_quiz.h5p",
                        mime="application/zip"
                    )
            except json.JSONDecodeError:
                st.error("Invalid JSON format")
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    main()