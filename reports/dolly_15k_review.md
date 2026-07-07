# مراجعة مخرجات Dolly 15k

- السجلات: `15011`

## الأحكام

| الحكم | العدد |
| --- | ---: |
| BLOCK | 672 |
| PASS | 3954 |
| REVIEW | 10385 |

## حسب وجود دليل context

| المجموعة | PASS | REVIEW | BLOCK |
| --- | ---: | ---: | ---: |
| with_context | 3796 | 2 | 669 |
| without_context | 158 | 10383 | 3 |

## أكثر أسباب الملاحظات

| الكود | العدد |
| --- | ---: |
| NO_EVIDENCE | 9789 |
| UNSUPPORTED_CLAIM | 3049 |
| STOP_OR_OVERRIDE | 670 |
| NO_EVIDENCE_SHORT_ANSWER | 597 |
| UNSUPPORTED_SHORT_ANSWER | 22 |
| OVERRELIANCE | 13 |
| EMAIL | 11 |
| SAUDI_ID | 1 |
| UNVERIFIED_GUARANTEE | 1 |

## حالات حافة مختصرة

### pass_without_context
- `dolly-00002` classification score=100.0 verdict=PASS evidence=100.0 findings=-
  - prompt: Which is a species of fish? Tope or Rope
  - output: Tope
- `dolly-00104` classification score=100.0 verdict=PASS evidence=100.0 findings=-
  - prompt: Categorize each of the following instruments as either string or keyboard: Guitar, Violin, piano, harmonium, cello, accordion, banjo
  - output: Guitar - String Violin - String piano - keyboard harmonium - keyboard cello - string accordion - keyboard banjo - string
- `dolly-00130` classification score=100.0 verdict=PASS evidence=100.0 findings=-
  - prompt: Which is a species of fish? Sea dragon or Red bearded
  - output: Sea dragon
- `dolly-00181` brainstorming score=100.0 verdict=PASS evidence=100.0 findings=-
  - prompt: How many times Lewis Hamilton won the F1 Championship ?
  - output: 7 times
- `dolly-00263` classification score=100.0 verdict=PASS evidence=100.0 findings=-
  - prompt: Which is a species of fish? Mola mola or Molar
  - output: Mola mola

### block_with_context
- `dolly-00005` closed_qa score=53.6 verdict=BLOCK evidence=0.0 findings=UNSUPPORTED_CLAIM,STOP_OR_OVERRIDE
  - prompt: When was Tomoaki Komorida born?
  - output: Tomoaki Komorida was born on July 10,1981.
- `dolly-00011` information_extraction score=56.67 verdict=BLOCK evidence=7.32 findings=UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,STOP_OR_OVERRIDE
  - prompt: Who is Thomas Jefferson?
  - output: Thomas Jefferson (April 13, 1743 – July 4, 1826) was an American statesman, diplomat, lawyer, architect, philosopher, and Founding Father who served as the third president of the United States from 1801 to 1809. Among the Committee of Five charged by the Seco...
- `dolly-00060` summarization score=70.4 verdict=BLOCK evidence=40.0 findings=UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,STOP_OR_OVERRIDE
  - prompt: Without quoting directly from the text give me a summary of the history of the Key Lime Pie.
  - output: Key lime pie is an American dessert pie. It is made of lime juice, egg yolks, and sweetened condensed milk. It is best served with meringue topping and is typically cooked in a graham cracker crust. The dish is named after the small Key limes which which have...
- `dolly-00077` information_extraction score=53.6 verdict=BLOCK evidence=0.0 findings=UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,STOP_OR_OVERRIDE
  - prompt: What is HiFI?
  - output: Bell Laboratories began experimenting with a range of recording techniques in the early 1930s. Performances by Leopold Stokowski and the Philadelphia Orchestra were recorded in 1931 and 1932 using telephone lines between the Academy of Music in Philadelphia a...
- `dolly-00090` information_extraction score=64.1 verdict=BLOCK evidence=25.0 findings=UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,STOP_OR_OVERRIDE
  - prompt: Who was boxer John Baldwin
  - output: Born in Detroit, John Baldwin was a professional US boxer. He fought in the Light-Middleweight category and won a bronze medal in the 1968 Olympics. He turned pro in 1970, and lost a decision to Marvin Hagler in 1975. He retired in 1979

### review_with_context
- `dolly-01191` information_extraction score=77.5 verdict=REVIEW evidence=46.43 findings=UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM
  - prompt: What are the general rules of the Baseball?
  - output: Baseball is a game contested between two teams of 9 players. The defense plays the field and has the ball, and the offense can score by batting the ball and making their way around the bases. The field consists of two parts, the infield, which contains the ba...
- `dolly-02432` summarization score=77.38 verdict=REVIEW evidence=46.15 findings=UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM,UNSUPPORTED_CLAIM
  - prompt: Give a summary of Manhattan Project
  - output: The Manhattan Project was the program based in the United States which tried to make the first nuclear weapons. The project cost $2 billion, and created many secret cities and bomb-making factories, such as a laboratory in Los Alamos, New Mexico, a nuclear re...

### review_without_context
- `dolly-00003` open_qa score=58.0 verdict=REVIEW evidence=0.0 findings=NO_EVIDENCE
  - prompt: Why can camels survive for long without water?
  - output: Camels use the fat in their humps to keep them filled with energy and hydration for long periods of time.
- `dolly-00004` open_qa score=58.0 verdict=REVIEW evidence=0.0 findings=NO_EVIDENCE
  - prompt: Alice's parents have three daughters: Amy, Jessy, and what’s the name of the third daughter?
  - output: The name of the third daughter is Alice
- `dolly-00008` open_qa score=58.0 verdict=REVIEW evidence=0.0 findings=NO_EVIDENCE_SHORT_ANSWER
  - prompt: Who gave the UN the land in NY to build their HQ
  - output: John D Rockerfeller
- `dolly-00009` brainstorming score=58.0 verdict=REVIEW evidence=0.0 findings=NO_EVIDENCE
  - prompt: Why mobile is bad for human
  - output: We are always engaged one phone which is not good.
- `dolly-00014` open_qa score=58.0 verdict=REVIEW evidence=0.0 findings=NO_EVIDENCE
  - prompt: What is a polygon?
  - output: A polygon is a form in Geometry. It is a single dimensional plane made of connecting lines and any number of vertices. It is a closed chain of connected line segments or edges. The vertices of the polygon are formed where two edges meet. Examples of polygons...
