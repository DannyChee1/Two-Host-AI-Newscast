from openai import OpenAI
from typing import List, Dict
import json


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

    system_prompt = _build_system_prompt(personas, target_duration, profanity_filter)
    user_prompt = _build_user_prompt(stories)
    
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,
            max_tokens=4000
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
        
        _validate_script(script_data, stories)
        
        return script_data

    except json.JSONDecodeError as e:
        raise ScriptGenerationError(f"Failed to parse response as JSON: {e}")
    except Exception as e:
        raise ScriptGenerationError(f"Unexpected error during script generation: {e}")

def _build_system_prompt(personas: Dict, target_duration: int, profanity_filter: bool) -> str:
    
    host1 = personas['hosts'][0]
    host2 = personas['hosts'][1]
    
    prompt = f"""You're writing an engaging podcast conversation that FLOWS naturally. Not a Q&A. Not an interview. A real conversation where people build on each other's thoughts.

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
- Contractions: "it's", "we're", "that's", "you're", "don't"
- Fillers: "I mean", "you know", "like", "honestly", "basically", "actually"
- Thinking: "Hmm", "Oh", "Well", "So", "Right"
- Interruptions: "Wait—" "Hold on—" "But—"

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

**TARGET**: ~{target_duration} minutes ({target_duration * 160} words)
- Mix VERY short (1-5 words) with LONG explanations (70-120 words)
- Let conversation flow and build
- NOT rapid-fire Q&A

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
    
    prompt += "Remember - Make it CONVERSATIONAL:\n"
    prompt += "- Natural back-and-forth with short reactions: 'Right', 'Exactly', 'Wait, what?', 'That's wild'\n"
    prompt += "- Use conversational filler: 'I mean', 'You know', 'Like', 'Actually'\n"
    prompt += "- Mix short (3-10 word) reactions with longer (30-50 word) explanations\n"
    prompt += "- Aim for 25-35 dialogue exchanges per story (not 5-8 monologues)\n"
    prompt += "- Every fact must have [src: i] annotation\n"
    prompt += "- Make the hosts sound distinctly different in vocabulary and energy\n"
    prompt += "- Dive deeper: ask questions, explore implications, add context\n"
    prompt += "- Include callbacks to earlier moments\n"
    prompt += "- Return ONLY valid JSON (no markdown code blocks)\n"
    
    return prompt


def _validate_script(script_data: Dict, stories: List[Dict]) -> None:
    if 'rundown' not in script_data:
        raise ScriptGenerationError("Script missing 'rundown' key")
    if 'dialogue' not in script_data:
        raise ScriptGenerationError("Script missing 'dialogue' key")
    
    segments = [seg.get('segment', '') for seg in script_data['rundown']]
    if 'cold_open' not in segments:
        raise ScriptGenerationError("Script missing cold_open segment")
    if 'kicker' not in segments:
        raise ScriptGenerationError("Script missing kicker segment")

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
    