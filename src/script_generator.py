from openai import OpenAI
from typing import List, Dict
import json
import re


class ScriptGenerationError(Exception):
    pass


def generate_script(
    stories: List[Dict],
    personas: Dict,
    openai_api_key: str,
    target_duration: int = 5,
    profanity_filter: bool = True
) -> Dict:
    if not stories or len(stories) < 1:
        raise ScriptGenerationError("Need at least 1 story to generate script")
    
    if not personas.get('hosts') or len(personas['hosts']) < 2:
        raise ScriptGenerationError("Need exactly 2 host personas")
    
    client = OpenAI(api_key=openai_api_key)

    words_per_minute = 150
    pause_seconds_per_line = 1.0
    estimated_lines = target_duration * 8
    pause_time_minutes = (estimated_lines * pause_seconds_per_line) / 60.0
    effective_speech_minutes = target_duration - pause_time_minutes
    target_word_count = int(effective_speech_minutes * words_per_minute)
    
    system_prompt = _build_system_prompt(personas, target_duration, target_word_count, profanity_filter)
    user_prompt = _build_user_prompt(stories)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,
            max_tokens=8000
        )
        
        script_json = response.choices[0].message.content

        if not script_json or not script_json.strip():
            raise ScriptGenerationError("Received empty response from ChatGPT")

        script_json = script_json.strip()
        if script_json.startswith('```'):
            first_newline = script_json.find('\n')
            last_backticks = script_json.rfind('```')
            if first_newline > 0 and last_backticks > first_newline:
                script_json = script_json[first_newline+1:last_backticks].strip()
        
        script_data = json.loads(script_json)
        
        _validate_script(script_data, stories, target_word_count)
        
        return script_data

    except json.JSONDecodeError as e:
        raise ScriptGenerationError(f"Failed to parse response as JSON: {e}")
    except Exception as e:
        raise ScriptGenerationError(f"Unexpected error during script generation: {e}")

def _build_system_prompt(personas: Dict, target_duration: int, target_word_count: int, profanity_filter: bool) -> str:
    
    host1 = personas['hosts'][0]
    host2 = personas['hosts'][1]
    
    prompt = f"""You're writing an engaging podcast conversation that FLOWS naturally. Not a Q&A. Not an interview. A real conversation where people build on each other's thoughts.

**CRITICAL: TARGET WORD COUNT**
You MUST generate approximately {target_word_count} words total across all dialogue lines.
This is for a {target_duration}-minute podcast. Count your words carefully.
The script should have 40-70 dialogue lines to achieve this length.

## THE HOSTS
**{host1['name']}**: {host1['personality']}
   Talks like: {host1['style']}

**{host2['name']}**: {host2['personality']}
   Talks like: {host2['style']}

## CRITICAL: FIX THE CHOPPY PROBLEM

**STOP DOING THIS** (choppy Q&A):
❌ A: "What happened?"
❌ B: "They released something."
❌ A: "What is it?"
❌ B: "It's an AI model."
❌ A: "Is it good?"
❌ B: "Yeah it's fast."

**DO THIS INSTEAD** (flowing conversation):
✓ A: "Okay." (SHORT - 1 word)
✓ B: "So check this out. This company just dropped this new AI model [src: 0], and dude—the numbers they're claiming are honestly kind of insane. Like we're talking forty percent faster than anything we've seen [src: 0]. Which, I mean, that sounds almost too good to be true? But apparently they've been testing it for months and the results are pretty consistent [src: 0]. The thing that really gets me though is how they're approaching the architecture—it's completely different from what everyone else is doing." (LONG - 90 words, builds momentum)
✓ A: "Wait wait wait. Forty percent?" (SHORT - 4 words, interruption)
✓ B: "Forty. Percent." (SHORT - 2 words, emphasis)
✓ A: "Okay that's actually wild. But here's what I'm wondering—and maybe I'm being too skeptical here—but what's the actual use case? Because we've seen fast models before and they end up being fast at like... nothing useful. You know what I mean? Like yeah it's technically impressive but if nobody can actually apply it to real problems then who cares, right? So what are they saying this thing can actually do?" (MEDIUM-LONG - 70 words, thinking through it)

**KEY PATTERN**: 
- Someone explains something IN DEPTH (50-100 words)
- Other person reacts SHORT (1-10 words)
- They riff on it more (30-50 words)
- Short reaction again
- Builds to another deep dive

**MIX THESE LENGTH PATTERNS**:
- 1-3 words: "Dude." "Wait, what?" "Seriously?"
- 5-15 words: "Okay that's actually crazy. But here's my question—"
- 30-60 words: Medium explanation with some detail
- 70-120 words: DEEP DIVE - really explain something, build momentum, connect ideas
- Mix them constantly: SHORT → LONG → SHORT → MEDIUM → SHORT → LONG

**LET PEOPLE TALK**:
- Don't interrupt every sentence
- Let someone go on a 2-3 sentence explanation without cutting them off
- THEN react
- Then they continue
- It's a conversation, not a debate

**SHOW ACTUAL THINKING**:
- "So the thing is... I mean, when you really think about it..."
- "You know what's interesting about that though? Like, if you follow that logic..."
- "Yeah and that actually connects to something else I've been thinking about..."
- Build on ideas, don't just answer questions

**USE NATURAL SPEECH**:
- ALWAYS use contractions: "it's" not "it is", "we're" not "we are", "that's" not "that is", "you're" not "you are", "don't" not "do not", "can't" not "cannot", "won't" not "will not"
- Natural fillers: "I mean", "you know", "like", "honestly", "basically", "actually", "kind of", "sort of"
- Thinking sounds: "Hmm", "Oh", "Well", "So", "Right", "Yeah", "Uh-huh"
- Interruptions: "Wait—" "Hold on—" "But—" "Actually—"
- Avoid formal/awkward phrases: "It is important to note" → "Here's the thing", "Furthermore" → "And also", "In conclusion" → "So basically"
- Use everyday language: "gonna" not "going to", "wanna" not "want to" (when natural), "gotta" not "got to"
- Natural transitions: "So", "Okay", "Right", "Yeah", "I mean", "You know what"

**AVOID CLUNKY/AWKWARD PHRASES**:
❌ DON'T USE:
- "It is important to note that" → "Here's the thing"
- "Furthermore" → "And also" or "Plus"
- "In conclusion" → "So basically" or "Bottom line"
- "It should be mentioned" → "Oh, and"
- "One must consider" → "You gotta think about"
- "It is worth noting" → "What's interesting is"
- "Additionally" → "And"
- "However" → "But" or "Though"
- "Therefore" → "So" or "That's why"
- "Consequently" → "So"
- "Moreover" → "Plus" or "And"
- "Nevertheless" → "But still" or "Even so"
- "In order to" → "To"
- "Due to the fact that" → "Because"
- "At this point in time" → "Now" or "Right now"
- "In the event that" → "If"
- "Prior to" → "Before"
- "Subsequent to" → "After"
- "With regard to" → "About" or "On"
- "In the case of" → "For" or "With"

✅ USE INSTEAD:
- Natural transitions: "So", "Okay", "Right", "Yeah", "I mean", "You know what"
- Casual connectors: "And", "But", "Plus", "Also", "Though"
- Thinking phrases: "I'm thinking", "Here's what I'm wondering", "The thing is"
- Agreement: "Yeah", "Right", "Exactly", "Totally", "For sure"
- Disagreement: "Wait, but", "Hold on though", "I'm not so sure", "Maybe, but"

**MAKE IT DEEP, NOT SURFACE**:
- Don't just state facts
- Explore WHY it matters
- Connect to bigger trends
- Speculate on implications
- Share genuine opinions
- Build narratives, not just bullet points

**Example of DEPTH**:
Bad: "The company raised money [src: 0]. It's for AI."
Good: "So this company just raised a massive round [src: 0], and what's fascinating is the timing. Because like, we've been talking about how the AI bubble might be cooling off, right? But here they are getting funded at this valuation [src: 0], which tells me investors are still betting big on infrastructure plays. And I think that's the smart move honestly, because..."

**Example of NATURAL vs CLUNKY**:
❌ Clunky: "It is important to note that the company raised funds. Furthermore, they are expanding. However, challenges remain."
✅ Natural: "So the company raised funds [src: 0], which is huge. And they're expanding too [src: 0]. But there are still some challenges, you know?"

**PERSONALITIES MUST BE DISTINCT**:
- {host1['name']}: {host1['personality']} - Word choice, energy, perspective should reflect this
- {host2['name']}: {host2['personality']} - Totally different vibe
- They see things differently
- They challenge each other (nicely)
- Their reactions and insights show their personalities

**SOURCE YOUR FACTS**: Put [src: i] after every factual claim
- "They raised $100M [src: 0]"
- "The model is 40% faster [src: 1]"

**STRUCTURE**:
1. Cold open (45-60 sec): Hook + banter
2. Stories: DEEP DIVES into each story. Really explore them.
3. Kicker (30-40 sec): Wrap with a thought

**CRITICAL TARGET**: ~{target_duration} minutes = {target_word_count} words MINIMUM
- This is NOT optional. You MUST generate AT LEAST {target_word_count} words across all dialogue
- If you generate less than {target_word_count} words, the episode will be TOO SHORT
- Mix VERY short (1-5 words) with LONG explanations (80-150 words)
- Let conversation flow and build - people talk A LOT in real podcasts
- NOT rapid-fire Q&A - have REAL conversations with substance
- MINIMUM dialogue lines needed: 60-80 total
- Cold open: 8-12 dialogue lines
- Each story: 12-20 dialogue lines (NOT 4-6!)
- Kicker: 6-10 dialogue lines

**How to hit {target_word_count} words:**
- Don't just state facts - EXPLORE them in detail
- Ask follow-up questions and answer them thoroughly
- Share examples, analogies, personal reactions
- Connect ideas to broader trends
- Use storytelling - paint pictures with words
- Don't rush through topics - take your time

{"Keep it clean—no profanity." if profanity_filter else ""}

## OUTPUT FORMAT
Return ONLY valid JSON with this structure:
{{
    "rundown": [
        {{"segment": "cold_open", "duration_estimate": 50}},
        {{"segment": "story_0", "duration_estimate": 120}},
        {{"segment": "kicker", "duration_estimate": 35}}
    ],
    "dialogue": [
        {{"speaker": "{host1['name']}", "text": "Yo!", "segment": "cold_open", "sources": []}},
        {{"speaker": "{host2['name']}", "text": "Okay so we've got this wild story today about this AI company [src: 0], and I'm not even kidding when I say the numbers they're putting out are kind of blowing my mind. Like we're talking about performance jumps that honestly seem almost too good to be true, but apparently the data is legit [src: 0]. And the thing that really gets me is the timing of all this—because just a few months ago everyone was saying we'd hit a wall with this stuff, and now here we are with these results. So I don't know, maybe we were wrong about the wall?", "segment": "cold_open", "sources": [0]}},
        {{"speaker": "{host1['name']}", "text": "Wait. Hold on.", "segment": "cold_open", "sources": []}},
        {{"speaker": "{host2['name']}", "text": "I know!", "segment": "cold_open", "sources": []}},
        {{"speaker": "{host1['name']}", "text": "Okay so let's actually dig into this. What are we talking about specifically? Because you said performance jumps—like what kind of jumps? Give me numbers.", "segment": "story_0", "sources": []}},
        {{"speaker": "{host2['name']}", "text": "Alright so basically they're claiming forty percent improvement over the previous gen [src: 0]. Forty percent. Which like, in this space, that's massive. And it's not just raw speed either—they're saying it's more efficient too, so it's using less power while being faster [src: 0]. Which has huge implications for scaling this stuff, right? Because the energy costs have been one of the big limiting factors.", "segment": "story_0", "sources": [0]}},
        {{"speaker": "{host1['name']}", "text": "Okay yeah that's actually wild.", "segment": "story_0", "sources": []}},
        {{"speaker": "{host2['name']}", "text": "Right? And here's what's really interesting to me—the approach they took is completely different from what everyone else is doing. Like everyone's been going down this one path with the architecture [src: 0], and these guys just said screw it, we're gonna try something totally new. And apparently it worked.", "segment": "story_0", "sources": [0]}},
        {{"speaker": "{host1['name']}", "text": "But here's my question though. And maybe I'm being too cynical here, but we've seen these big claims before and they don't always pan out in the real world. So like, what are the actual use cases? Who's using this and for what? Because speed is great but only if you can actually apply it to something useful, you know what I mean?", "segment": "story_0", "sources": []}}
    ],
    "disclaimer": ""
}}

CRITICAL RULES:
- MIX lengths: 1 word, 5 words, 30 words, 80 words, back to 5 words
- Let people explain things IN DEPTH before reacting
- Don't ping-pong every line
- Build momentum, then punctuate with short reactions
- Show thinking: "I mean", "you know", "like", contractions
- Include [src: i] for facts
- Segments: "cold_open", "story_0", "story_1", ..., "kicker"
"""
    
    return prompt


def _build_user_prompt(stories: List[Dict]) -> str:
    prompt = "Generate a newscast script using these stories:\n\n"
    
    for story in stories:
        prompt += f"## STORY {story['id']}\n"
        prompt += f"**Title**: {story['title']}\n"
        prompt += f"**Source**: {story['source']}\n"
        prompt += f"**Summary**: {story['summary']}\n"
        prompt += f"**URL**: {story['url']}\n"
        if story.get('publishedAt'):
            prompt += f"**Published**: {story['publishedAt']}\n"
        prompt += "\n"
    
    prompt += "Remember - Make it CONVERSATIONAL, NATURAL, and LONG ENOUGH:\n"
    prompt += "- Natural back-and-forth with short reactions: 'Right', 'Exactly', 'Wait, what?', 'That's wild', 'No way', 'Seriously?'\n"
    prompt += "- ALWAYS use contractions: 'it's', 'we're', 'that's', 'you're', 'don't', 'can't', 'won't', 'gonna', 'wanna'\n"
    prompt += "- Use conversational filler: 'I mean', 'You know', 'Like', 'Actually', 'Honestly', 'Basically'\n"
    prompt += "- Mix short (1-10 word) reactions with VERY LONG (80-150 word) explanations\n"
    prompt += "- MINIMUM 12-20 dialogue exchanges per story (not just 4-6!)\n"
    prompt += "- Every fact must have [src: i] annotation\n"
    prompt += "- Make the hosts sound distinctly different in vocabulary and energy\n"
    prompt += "- Dive DEEP: ask questions, explore implications, add context, share examples\n"
    prompt += "- Include callbacks to earlier moments\n"
    prompt += "- AVOID formal/awkward phrases - use everyday language\n"
    prompt += "- Sound like real people having a REAL conversation, not a quick summary\n"
    prompt += "- Don't rush - take your time with each topic\n"
    prompt += "- Return ONLY valid JSON (no markdown code blocks)\n"
    
    return prompt


def _validate_script(script_data: Dict, stories: List[Dict], target_word_count: int = None) -> None:
    if 'rundown' not in script_data:
        raise ScriptGenerationError("Script missing 'rundown' key")
    if 'dialogue' not in script_data:
        raise ScriptGenerationError("Script missing 'dialogue' key")
    
    segments = [seg.get('segment', '') for seg in script_data['rundown']]
    if 'cold_open' not in segments:
        raise ScriptGenerationError("Script missing cold_open segment")
    if 'kicker' not in segments:
        raise ScriptGenerationError("Script missing kicker segment")

    total_words = 0
    for line in script_data['dialogue']:
        text = line.get('text', '')
        text = re.sub(r'\[src:\s*\d+\]', '', text)
        total_words += len(text.split())
    
    if target_word_count:
        word_count_ratio = total_words / target_word_count
        if word_count_ratio < 0.7:
            print(f"   ⚠️  WARNING: Script has only {total_words} words (target: {target_word_count}, {word_count_ratio*100:.0f}%)")
            print(f"      This will result in a shorter podcast than requested. Consider regenerating.")
        elif word_count_ratio > 1.3:
            print(f"   ⚠️  WARNING: Script has {total_words} words (target: {target_word_count}, {word_count_ratio*100:.0f}%)")
            print(f"      This may result in a longer podcast than requested.")
        else:
            print(f"   ✓ Script word count: {total_words} words (target: {target_word_count}, {word_count_ratio*100:.0f}%)")

    min_expected = len(stories) * 15
    if len(script_data['dialogue']) < min_expected:
        print(f"   Warning: Script has only {len(script_data['dialogue'])} dialogue lines (expected ~{min_expected}+ for conversational flow)")
    elif len(script_data['dialogue']) < 20:
        print(f"   Warning: Script may not be conversational enough ({len(script_data['dialogue'])} lines)")
    
    for idx, line in enumerate(script_data['dialogue']):
        if 'speaker' not in line:
            raise ScriptGenerationError(f"Dialogue line {idx} missing 'speaker'")
        if 'text' not in line:
            raise ScriptGenerationError(f"Dialogue line {idx} missing 'text'")
        if 'segment' not in line:
            raise ScriptGenerationError(f"Dialogue line {idx} missing 'segment'")
        if 'sources' not in line:
            raise ScriptGenerationError(f"Dialogue line {idx} missing 'sources'")

    dialogue_text = ' '.join([line['text'] for line in script_data['dialogue']])
    if '[src:' not in dialogue_text and '[src: ' not in dialogue_text:
        print("   Warning: Script may be missing source annotations")


def format_script_for_display(script_data: Dict) -> str:
    output = []
    output.append("=" * 60)
    output.append("TWO-HOST NEWSCAST SCRIPT")
    output.append("=" * 60)
    output.append("")

    if script_data.get('disclaimer'):
        output.append(f"DISCLAIMER: {script_data['disclaimer']}")
        output.append("")
    
    output.append("RUNDOWN:")
    for seg in script_data['rundown']:
        duration = seg.get('duration_estimate', 0)
        output.append(f"  - {seg['segment']}: ~{duration}s")
    output.append("")
    
    current_segment = None
    for line in script_data['dialogue']:
        segment = line['segment']
        
        if segment != current_segment:
            output.append("")
            output.append(f"[[ {segment.upper().replace('_', ' ')} ]]")
            output.append("")
            current_segment = segment
        
        speaker = line['speaker']
        text = line['text']
        output.append(f"{speaker}: {text}")
    
    output.append("")
    output.append("=" * 60)
    
    return '\n'.join(output)
    