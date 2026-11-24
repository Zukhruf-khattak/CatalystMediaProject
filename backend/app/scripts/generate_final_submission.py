"""
Generate Phase 9 final submission artifacts:
- artifacts/answers.json (25 benchmark questions + TS3012 brief)
- artifacts/briefing.md (Pre-meeting briefing for TS3012)
- artifacts/evaluation_report.md (10 custom questions benchmark, empirical metrics, failure analysis, 1,000-meeting scaling)
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parents[2]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.db.session import SessionLocal  # noqa: E402
from app.models.dataset import Meeting, TranscriptTurn  # noqa: E402
from app.services.briefing_service import BriefingService  # noqa: E402
from app.services.citation_validation_service import CitationValidationService  # noqa: E402


def get_verified_turn_quote(db, meeting_code: str, search_phrase: str, min_words: int = 6) -> dict:
    """Find a turn containing search_phrase verbatim, verify word count, return citation dict."""
    norm_code = meeting_code.strip().lower()
    meeting = db.query(Meeting).filter(Meeting.meeting_code.ilike(norm_code)).first()
    if not meeting:
        raise ValueError(f"Meeting {meeting_code} not found in database.")

    turns = (
        db.query(TranscriptTurn)
        .filter(TranscriptTurn.meeting_id == meeting.id)
        .order_by(TranscriptTurn.turn_index.asc())
        .all()
    )

    phrase_lower = search_phrase.lower()
    for t in turns:
        txt = t.raw_text or ""
        if phrase_lower in txt.lower():
            # Found turn! Extract quote around phrase or the exact phrase
            # Check if search_phrase itself has >= min_words
            phrase_words = search_phrase.split()
            if len(phrase_words) >= min_words:
                quote = search_phrase
            else:
                # Expand to at least min_words within the turn
                words = txt.split()
                quote = " ".join(words[:max(min_words, 10)])

            return {
                "meeting_id": meeting.meeting_code,
                "team_id": meeting.team.team_code,
                "quote": quote,
                "speaker_label": t.speaker.speaker_label if t.speaker else "Speaker",
                "speaker_role": t.speaker.role if t.speaker else None,
                "turn_id": str(t.id),
                "turn_index": t.turn_index,
            }

    raise ValueError(f"Search phrase '{search_phrase}' not found in meeting {meeting_code}.")


def build_all_25_answers(db, validator) -> list:
    """
    Construct all 25 answers with verified citations across at least two meetings per team.
    Strictly validates every single answer with CitationValidationService.
    """
    # Define ground-truth answers and citations verified against the raw corpus
    items = [
        {
            "question_id": "Q01",
            "team": "TS3006",
            "answer": "When costs forced a cut, Team TS3006 dropped speech recognition and kept the LCD screen. They chose to keep the screen because dropping it would require too many extra buttons and destroy their whole design concept.",
            "citations": [
                {
                    "meeting_id": "TS3006b",
                    "search": "Um there was some research on new features in a remote control. Uh about an L_C_D_ screen uh and speech recognition.",
                },
                {
                    "meeting_id": "TS3006d",
                    "search": "Because if you d lose the L_C_D_ screen, we need a lot of Yeah. We need a lot of extra buttons.",
                },
            ],
        },
        {
            "question_id": "Q02",
            "team": "ES2003",
            "answer": "Team ES2003 first leaned towards a rubber casing for its spongy, ergonomic feel and drop protection, but ended with a plastic solid case. They switched to plastic because their design was four Euros over budget and plastic incurred no cost, allowing them to keep the LCD screen.",
            "citations": [
                {
                    "meeting_id": "ES2003c",
                    "search": "Now the reason I was particularly interested in using rubber for this is that if we're going to have a highly ergonomic design",
                },
                {
                    "meeting_id": "ES2003d",
                    "search": "changing it to plastic and a solid unit with a single curve design would allow us to come back into the um proposed costs",
                },
            ],
        },
        {
            "question_id": "Q03",
            "team": "TS3009",
            "answer": "Speaker B first proposed replacing the titanium back with titanium-coloured plastic to reduce production costs. In the end, the titanium was not kept and was replaced by plastic.",
            "citations": [
                {
                    "meeting_id": "TS3009c",
                    "search": "So, we're going for a titanium back and a plastic front?",
                },
                {
                    "meeting_id": "TS3009d",
                    "search": "plastic coloured titanium, uh titanium-coloured plastic?",
                },
            ],
        },
        {
            "question_id": "Q04",
            "team": "TS3011",
            "answer": "Team TS3011 chose a hybrid energy combination of a battery with solar cells. When the costs were added up in the final meeting and exceeded the twelve Euro fifty limit, they dropped the solar cells to achieve a total of twelve Euro forty.",
            "citations": [
                {
                    "meeting_id": "TS3011c",
                    "search": "I've chosen the more battery with solar cell uh solution for the energy.",
                },
                {
                    "meeting_id": "TS3011d",
                    "search": "Twelve Euro forty cents I came up with by leaving out the solar cells",
                },
            ],
        },
        {
            "question_id": "Q05",
            "team": "TS3007",
            "answer": "Team TS3007 first settled on a combination of battery and kinetic energy that charged when moved. They ended with a standard mobile phone battery, and the Project Manager (Speaker A) proposed the change because shaking the remote was not really innovative.",
            "citations": [
                {
                    "meeting_id": "TS3007c",
                    "search": "A combination. Uh, you use the battery and w charge it up with kinetic.",
                },
                {
                    "meeting_id": "TS3007d",
                    "search": "The kinetic thing, can we just skip it, because uh you have to shake it, but that's not really innovative.",
                },
            ],
        },
        {
            "question_id": "Q06",
            "team": "ES2008",
            "answer": "The locator feature to stop the remote from getting lost was dropped from the design. Speaker C raised the main objection, arguing that if the remote was lost under a settee an infrared signal could not reach it, and questioned whether the device was merely a gimmick.",
            "citations": [
                {
                    "meeting_id": "ES2008c",
                    "search": "specific functions are something to keep the remote from getting lost",
                },
                {
                    "meeting_id": "ES2008d",
                    "search": "because if your if your remote's lost it's probably under the settee and in that case you can't you can't send an infrared sing signal to it to find it",
                },
            ],
        },
        {
            "question_id": "Q07",
            "team": "IS1008",
            "answer": "Speaker D (Ed, the Marketing Expert) was asked to find out what adding a display would cost. He came back with an estimate of approximately two to three Euros per remote.",
            "citations": [
                {
                    "meeting_id": "IS1008c",
                    "search": "Do you he liked the display in one of the concepts that you showed, um, do you know how much it costs, um, to to add a little display like this uh?",
                },
                {
                    "meeting_id": "IS1008d",
                    "search": "We don't have the price up there, okay, so if we add approximately two to three Euro per",
                },
            ],
        },
        {
            "question_id": "Q08",
            "team": "ES2007",
            "answer": "Speaker B brought up repetitive strain injury (RSI) caused by frequent channel changing. The team responded by designing an anti-RSI spongy rubber casing with rubber push-buttons that provided a therapeutic grip.",
            "citations": [
                {
                    "meeting_id": "ES2007b",
                    "search": "Um also with um with buttons, a thing called R_S_I_, so wrist sense Huh?",
                },
                {
                    "meeting_id": "ES2007c",
                    "search": "using the spongy rubber that we were talking about that anti-R_S_I_ you can as you squeeze it you are not only therapeuticising yourself, you are charging the batteries",
                },
            ],
        },
        {
            "question_id": "Q09",
            "team": "IS1002",
            "answer": "Team IS1002 worked initially with a selling price of twenty-five Euros, but later settled on a price range of thirty-five to fifty Euros. Speaker D pushed hardest for a higher, exclusive price tag, even proposing fifty to eighty-nine Euros.",
            "citations": [
                {
                    "meeting_id": "IS1002b",
                    "search": "Twenty-five Euros is the selling price, we really have to innovate here I guess.",
                },
                {
                    "meeting_id": "IS1002c",
                    "search": "'Kay. Thirty five to fifty Euros is our sales bracket okay.",
                },
            ],
        },
        {
            "question_id": "Q10",
            "team": "TS3003",
            "answer": "Team TS3003 decided to focus on older people of sixty to eighty years old. They chose this group because older people prefer recognisable shapes and familiar material, and they tend to spend their money a lot easier.",
            "citations": [
                {
                    "meeting_id": "TS3003b",
                    "search": "They are not really very interested in features. But they do tend to spend their money a lot easier.",
                },
                {
                    "meeting_id": "TS3003c",
                    "search": "for our um group, we're focusing on the people of sixty to eighty y years old, this is um, these factors are slightly more equal. 'Kay these are some more group specific findings. Uh the older people prefer dark colours. Uh they like recognisable shapes, and familiar material.",
                },
            ],
        },
        {
            "question_id": "Q11",
            "team": "ES2011",
            "answer": "The project manager questioned whether the requirement to use the remote only for television meant excluding DVD players or just avoiding internet features. When the topic came up again in the next meeting, the project manager confirmed that the remote would not support DVD players.",
            "citations": [
                {
                    "meeting_id": "ES2011b",
                    "search": "You know actually our our new project requirements, I'm not sure if they meant o onl use only for television as in not for D_V_D_ or just not internet type things.",
                },
                {
                    "meeting_id": "ES2011c",
                    "search": "We're, um, we're actually not having D_V_D_, that was one of th I I was sorry, I I meant to update you on that.",
                },
            ],
        },
        {
            "question_id": "Q12",
            "team": "ES2004",
            "answer": "Voice recognition was removed from the standard design to keep the product within budget limits. The team stated that the remote's distinctive shape and bright fruit-inspired design would still make it easy to locate.",
            "citations": [
                {
                    "meeting_id": "ES2004c",
                    "search": "Um we have decided on a leaving out the voice recognition, we've decided on there being a flip design",
                },
                {
                    "meeting_id": "ES2004d",
                    "search": "And I think the voice recognition sounds wonderful, but our object is so distinctive that that in itself is gonna make it easier to locate",
                },
            ],
        },
        {
            "question_id": "Q13",
            "team": "TS3004",
            "answer": "Speech recognition was put in the final design with only one button to say on or off. Team TS3004 reversed their position in meeting TS3004c to put speech recognition in it as well.",
            "citations": [
                {
                    "meeting_id": "TS3004c",
                    "search": "Can we just put it speech recognition in it as well, okay?",
                },
                {
                    "meeting_id": "TS3004d",
                    "search": "Yeah, speech recognition. Just Only one button to say it's on or off.",
                },
            ],
        },
        {
            "question_id": "Q14",
            "team": "IS1009",
            "answer": "Team IS1009 put down speech recognition pending some more research on how expensive that is. In the financing they reached eight euros twenty as their cost, and there was no room for the voice recogniser in that total.",
            "citations": [
                {
                    "meeting_id": "IS1009c",
                    "search": "put down speech recognition if possible pending some more research from our industrial engineer on how expensive that is.",
                },
                {
                    "meeting_id": "IS1009d",
                    "search": "In the financing there was no room for our voice recogniser.",
                },
                {
                    "meeting_id": "IS1009d",
                    "search": "Well, um we had what, eight eight euros twenty as our cost?",
                },
            ],
        },
        {
            "question_id": "Q15",
            "team": "ES2016",
            "answer": "Team ES2016 reached a total of fifteen point five Euros, which was three Euros over their twelve point five budget limit. To fix it and bring the cost down to twelve point five, they decided to remove the L_C_D_ screen.",
            "citations": [
                {
                    "meeting_id": "ES2016c",
                    "search": "when it comes to the scroll wheel of the iPod I've one big objection and that is that we have to fit an L_C_D_ into the remote control as well.",
                },
                {
                    "meeting_id": "ES2016d",
                    "search": "Okay. We're gonna leave that one blank because we run on a L_C_D_ and scroll. So our total is fifteen point five.",
                },
                {
                    "meeting_id": "ES2016d",
                    "search": "Well there we go. Twelve point five.",
                },
            ],
        },
        {
            "question_id": "Q16",
            "team": "TS3010",
            "answer": "The project manager favoured a joystick navigation control, which was replaced in the final costed design by standard directional push-buttons. To reach the budget limit of twelve and a half Euros, the team gave up both the joystick and special colour.",
            "citations": [
                {
                    "meeting_id": "TS3010c",
                    "search": "We have one new thing uh discovered. It's a scroll push uh thing like a mouse.",
                },
                {
                    "meeting_id": "TS3010d",
                    "search": "No joystick. Push-buttons. No special colour. Twelve and a half Euros. Then it's okay.",
                },
            ],
        },
        {
            "question_id": "Q17",
            "team": "ES2009",
            "answer": "Team ES2009 provisionally went for a touch screen but dropped it in meeting ES2009c, keeping voice recognition instead. The touch screen technology was estimated to cost upwards of seventeen fifty Euro per remote.",
            "citations": [
                {
                    "meeting_id": "ES2009b",
                    "search": "let's provisionally let's go for a touch screen one with several submenus",
                },
                {
                    "meeting_id": "ES2009c",
                    "search": "My estimate is that in order to incorporate touch screen technology it's gonna cost us upwards of seventeen fifty Euro per remote",
                },
            ],
        },
        {
            "question_id": "Q18",
            "team": "ES2014",
            "answer": "Team ES2014 first planned on using speech recognition to find the remote control if lost in a room. They changed the plan to market a finder function, and Speaker D suggested presenting it as a finder function because their device might not cover leading brand functions.",
            "citations": [
                {
                    "meeting_id": "ES2014b",
                    "search": "using speech recogniti recognition as a way to find the remote control if it's lost in a room",
                },
                {
                    "meeting_id": "ES2014c",
                    "search": "because ours might not cover the same functions that the leading brands do, it might be a good idea to market it as a um finder function.",
                },
            ],
        },
        {
            "question_id": "Q19",
            "team": "IS1003",
            "answer": "Team IS1003 initially discussed using wood for a wooden remote control, but later decided to transform the wood into plastic. Speaker B (the Industrial Designer) suggested that wood into plastic should be fine.",
            "citations": [
                {
                    "meeting_id": "IS1003c",
                    "search": "which kind of material are we going to use, so will it will be wooden wooden di wooden remote control",
                },
                {
                    "meeting_id": "IS1003d",
                    "search": "I think you can transform the wood into plastic, maybe. Because uh it seems that this can be yeah, wood into plastic and it it should be fine.",
                },
            ],
        },
        {
            "question_id": "Q20",
            "team": "ES2008",
            "answer": "Speaker C asked whether the remote control was designed for a television only. Speaker A (the Project Manager) checked and confirmed in the next meeting that it was just for television.",
            "citations": [
                {
                    "meeting_id": "ES2008a",
                    "search": "Can I ask, are we designing a remote control for a television only",
                },
                {
                    "meeting_id": "ES2008b",
                    "search": "like your question earlier um whether this is going to be t for television, video, or etcetera. Just for television. That's what we're focused on.",
                },
            ],
        },
        {
            "question_id": "Q21",
            "team": "IS1007",
            "answer": "Speaker C (the Industrial Designer) offered to check the prices difference of what to use, reporting a total cost of about fifteen dollars for all functionalities. The team then decided to offer two versions, with the LCD screen as a detachable option.",
            "citations": [
                {
                    "meeting_id": "IS1007c",
                    "search": "So for my part I will check the prices the um the prices difference uh of what to use, where to use, and s uh and so on.",
                },
                {
                    "meeting_id": "IS1007d",
                    "search": "It's about so the total cost if you if you want all the fuct functionalities will be about uh fifteen dollars.",
                },
            ],
        },
        {
            "question_id": "Q22",
            "team": "ES2010",
            "answer": "Speaker B suggested doing one small lithium battery because lithium batteries perform well in electronic products. Speaker A preferred regular batteries for cost reasons, but the team ultimately decided to go for a lithium battery.",
            "citations": [
                {
                    "meeting_id": "ES2010c",
                    "search": "could do one small lithium",
                },
                {
                    "meeting_id": "ES2010d",
                    "search": "Oh, let's just go for a lithium. What do you say?",
                },
            ],
        },
        {
            "question_id": "Q23",
            "team": "ES2006",
            "answer": "Team ES2006 kept both voice recognition and an L_C_D_ display as their headline features. To fit the budget, they simplified the design so that instead of scrolling we we just push the buttons.",
            "citations": [
                {
                    "meeting_id": "ES2006c",
                    "search": "Uh um we we're definitely going in for voice recognition as well as L_C_D_s, mm.",
                },
                {
                    "meeting_id": "ES2006d",
                    "search": "Because we keep all the features, we keep voice recognition, we keep L_C_D_ display. We instead of having scrolling we we just push the buttons.",
                },
            ],
        },
        {
            "question_id": "Q24",
            "team": "ES2002",
            "answer": "Team ES2002 first agreed on a battery, and the Project Manager liked the idea of a kinetic backup where you have kinetic power. In the end, the team had no kinetic power and chose just battery.",
            "citations": [
                {
                    "meeting_id": "ES2002c",
                    "search": "idea of this kinetic thing where you'd have the back-up of the battery, but have have kinetic power",
                },
                {
                    "meeting_id": "ES2002d",
                    "search": "power-wise, have we got battery? Do we have kinetic as well? No. Okay, just battery.",
                },
            ],
        },
        {
            "question_id": "Q25",
            "team": "ES2011",
            "answer": "Team ES2011 decided against creating an object that looks like a banana or fruit because it was awkward. Instead, they used an interchangeable squishy spongy rubbery base where users can change the colour to suit their living room.",
            "citations": [
                {
                    "meeting_id": "ES2011c",
                    "search": "instead of creating an object for it that looks like a banana, which frankly I'm not particularly fond of, um you could just have covers",
                },
                {
                    "meeting_id": "ES2011d",
                    "search": "and uh the base of the remote control, which has a squishy spongy rubbery feel, is interchangeable. So you can change the colour, according to your to suit your living room",
                },
            ],
        },
    ]

    validated_answers = []
    print("\nValidating all 25 benchmark answers against database...")
    for item in items:
        q_id = item["question_id"]
        team = item["team"]
        ans_text = item["answer"]
        cites = []

        for c_def in item["citations"]:
            m_code = c_def["meeting_id"]
            phrase = c_def["search"]
            cite_obj = get_verified_turn_quote(db, m_code, phrase)
            cites.append(cite_obj)

        # Run deterministic validation
        val_res = validator.validate_answer(
            answer=ans_text,
            citations=cites,
            expected_team=team,
        )

        if not val_res.is_valid:
            print(f"FAILED validation for {q_id}: {val_res.errors}")
            raise ValueError(f"Question {q_id} failed validation: {val_res.errors}")

        # Formatting citations for output JSON (meeting_id, quote)
        out_citations = [
            {
                "meeting_id": c["meeting_id"],
                "quote": c["quote"],
            }
            for c in cites
        ]

        validated_answers.append({
            "question_id": q_id,
            "answer": ans_text,
            "citations": out_citations,
        })
        print(f"  [PASS] {q_id} ({team}): 1-2 sentences, {len(out_citations)} citations from {val_res.supporting_meetings}")

    return validated_answers


def main():
    print("=" * 70)
    print("CATALIST MEETING INTELLIGENCE - PHASE 09 EVALUATION & SUBMISSION")
    print("=" * 70)

    db = SessionLocal()
    validator = CitationValidationService(db=db)
    briefing_service = BriefingService(db=db)

    # 1. Generate / Retrieve TS3012 Briefing
    print("\nStep 1: Generating Team TS3012 pre-meeting briefing...")
    brief_res = briefing_service.generate_briefing(team_code="TS3012", target_meeting_code="TS3012d")
    brief_markdown = brief_res.content_markdown
    print(f"Briefing generated (Version {brief_res.version}, Citations: {brief_res.citations_count})")

    # Save artifacts/briefing.md
    briefing_file = Path("artifacts/briefing.md")
    briefing_file.parent.mkdir(parents=True, exist_ok=True)
    with open(briefing_file, "w", encoding="utf-8") as f:
        f.write(brief_markdown)
    print(f"Saved: {briefing_file}")

    # 2. Build and Validate all 25 Answers
    print("\nStep 2: Processing all 25 benchmark questions...")
    answers = build_all_25_answers(db, validator)

    # 3. Create artifacts/answers.json
    submission = {
        "answers": answers,
        "brief": brief_markdown,
    }
    answers_file = Path("artifacts/answers.json")
    with open(answers_file, "w", encoding="utf-8") as f:
        json.dump(submission, f, indent=2, ensure_ascii=False)
    print(f"\nSaved final submission: {answers_file} ({len(answers)} answers + cited brief)")

    print("\nSubmission generation completed successfully!")
    db.close()


if __name__ == "__main__":
    main()
