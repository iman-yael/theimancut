-- Migration 004: controlled vocabulary. Use these tags only; define new ones here (never near-duplicates).
INSERT INTO tag VALUES
 ('sens:domestic_violence','Depicts or references intimate-partner/family violence'),
 ('sens:sexual_assault','Depicts or references sexual assault'),
 ('sens:coercive_control','Depicts controlling, intimidating or isolating behaviour'),
 ('sens:racism','Racist acts, language or systems depicted'),
 ('sens:slur','Contains a slur (audio or text)'),
 ('sens:child_abuse','Abuse of a minor depicted or referenced'),
 ('sens:self_harm','Suicide or self-harm depicted or referenced'),
 ('sens:graphic_injury','Visible serious injury or blood'),
 ('sens:minor_onscreen','A minor is on screen (extra review)'),
 ('layer:depicted','Shown on screen'),
 ('layer:implied','Implied but not shown'),
 ('layer:documented','Independently documented historically (needs CLM)'),
 ('spoiler:S0','No spoilers'),('spoiler:S1','Premise only'),('spoiler:S2','Mid-series development'),('spoiler:S3','Finale / major outcome'),
 ('format:scene_clip','Single standout scene'),('format:actor_spotlight','One performer'),('format:character_portrait','Portrait without full arc'),
 ('format:arc_montage','Evidence-backed change over time'),('format:relationship_montage','Two characters'),('format:thematic_study','Theme across characters'),
 ('format:historical_breakdown','History-led explainer'),('format:channel_intro','Brand/creator introduction'),
 ('mood:quiet','Quiet scene, reaction or silence carries it'),('mood:humor','Comic beat'),('mood:tension','Conflict/tension');
