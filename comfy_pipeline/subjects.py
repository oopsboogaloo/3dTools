"""Subject manifest for the Dino Weird West portrait set.

One entry per portrait. `desc` deliberately carries NO proper name -- naming a
character in the prompt makes Klein render a caption onto the plate (see README).
Names are composited afterwards by label.py.

Ages are written DOWN by 10-15 years against the design doc, because Klein
consistently renders people older than asked (README, "Two more Klein habits").

`faction` drives the token ring colour and reflects what PLAYERS know, not the
truth -- Pemberton reads as village despite being quietly complicit.

Temporary states from the design doc (jailed, poisoned, sick livestock) are
deliberately excluded: these are status effects, not appearance.
"""

VILLAGE, BANDIT, NEUTRAL = "village", "bandit", "neutral"

# Shared traits per household, so families actually resemble each other. Klein
# picks a face per seed, so without this the Reed children look unrelated to the Reeds.
FAM = {
    "thorne": "dark hair, pale grey eyes, a long straight nose",
    "reed": "sandy fair hair, narrow features, light eyes",
    "hargrove": "dark hair, strong dark brows, a square jaw",
    "vance": "wild dark curling hair, a wide mouth, dark eyes",
    "calder": "sun-browned skin, mid-brown hair, broad cheekbones",
    "sutter": "heavy strong bone structure, deep-set eyes, dark blond hair",
    "pemberton": "fair skin, fine straight features, cool light eyes",
}

CHARACTERS = [
    # --- The Blacksmith ---------------------------------------------------
    dict(slug="josiah_coyle", name="Josiah Coyle", faction=VILLAGE,
         desc="an exhausted heavily built blacksmith of about forty, once-powerful shoulders slumped and caved inward, a wild untrimmed beard matted with soot, deep hollow shadows under bloodshot eyes, grime worked into every crease of his face and knuckles, cracked blackened hands hanging open between his knees, a scorched torn leather forge apron over a filthy sweat-stained shirt",
         bg="a dim blacksmith's forge, an anvil and hanging tongs behind him, the banked fire glowing low"),

    # --- Preacher / Schoolteacher ------------------------------------------
    dict(slug="elias_thorne", name="Elias Thorne", faction=VILLAGE,
         desc="a lean upright widowed frontier preacher of about thirty-five, {thorne}, grey threading early at the temples, neatly kept, an old soldier's bearing still visible in the set of his shoulders, a plain black preacher's coat and white collar",
         bg="a bare timber schoolhouse chapel, rough benches and a small lectern behind him"),
    dict(slug="ruth_thorne", name="Ruth Thorne", faction=VILLAGE,
         desc="a quiet watchful girl of about twelve, {thorne}, hair pinned neatly back for schoolwork, a plain dark hand-me-down dress meticulously mended at the cuffs, a still self-possessed expression older than her years",
         bg="a bare timber schoolhouse, a slate and worn schoolbooks on the bench beside her"),
    dict(slug="caleb_thorne", name="Caleb Thorne", faction=VILLAGE,
         desc="a restless lanky boy of about nine, {thorne}, very pale grey eyes, untidy dark hair, knees scuffed and trousers worn through, unable to sit quite still for the exposure",
         bg="a bare timber schoolhouse doorway with hard daylight behind him"),
    dict(slug="agnes_whitfield", name="Agnes Whitfield", faction=VILLAGE,
         desc="a small stooped elderly woman, sharp grey eyes that miss nothing, thin white hair drawn back severely, wrapped in a heavy dark knitted shawl despite the heat, hands folded tight in her lap",
         bg="a modest parlour with a plain wooden cross on the wall behind her"),

    # --- Doctor / Vet -------------------------------------------------------
    dict(slug="nathaniel_reed", name="Dr. Nathaniel Reed", faction=VILLAGE,
         desc="a slight precise country doctor of about thirty, {reed}, thinning sandy hair with spectacles pushed up into it, careful hands stained faintly with iodine, a dark waistcoat with sleeves rolled to the elbow",
         bg="a cramped surgery, shelves of glass bottles and steel instruments behind him"),
    dict(slug="margaret_reed", name="Margaret Reed", faction=VILLAGE,
         desc="a warm practical woman of about twenty-eight, {reed}, a streak of grey at one temple she has stopped hiding, sleeves rolled above the elbow, a plain working dress and apron",
         bg="a doctor's household kitchen, a kettle and folded linens behind her"),
    dict(slug="thomas_reed", name="Thomas Reed", faction=VILLAGE,
         desc="a curious lanky boy of about eleven, all elbows and knees, {reed}, hair sticking up at the crown, sitting upright with his hands on his knees, leaning very slightly toward the camera with open fascination, a plain shirt and long trousers",
         bg="a cluttered country surgery, shelves of bottles and instruments behind him"),
    dict(slug="clara_reed", name="Clara Reed", faction=VILLAGE,
         desc="a solemn round-cheeked little girl of about four, {reed}, fine fair hair, a stuffed cloth toy clutched tight in one fist, staring gravely at the lens",
         bg="a modest parlour, a low chair and a rag rug behind her"),
    dict(slug="daniel_reed", name="Daniel Reed", faction=VILLAGE,
         desc="a dark-haired infant of about one year old, propped upright and swaddled in a pale shawl, wide unfocused eyes, chubby hands splayed, a single tuft of dark hair",
         bg="a deep upholstered parlour chair with a lace cloth draped behind him"),
    dict(slug="walter_reed", name="Walter Reed", faction=VILLAGE,
         desc="a thin silver-haired elderly man, {reed}, sitting straight though he moves slowly, a worn but carefully brushed jacket, gentle patient eyes",
         bg="a modest parlour window seat, afternoon light falling across bare boards"),
    dict(slug="edith_reed", name="Edith Reed", faction=VILLAGE,
         desc="a small sharp-tongued elderly woman with a formidable set to her mouth, white hair in a tight bun, knitting needles and yarn resting in her lap, an appraising stare",
         bg="a modest parlour, a workbasket on the table beside her"),

    # --- Mayor / General Store ---------------------------------------------
    dict(slug="constance_hargrove", name="Constance Hargrove", faction=VILLAGE,
         desc="a handsome formidable woman of about thirty-five, {hargrove}, iron-grey streaks through dark hair worn severely pinned, a well-cut dark high-necked dress, absolutely upright, commanding the frame without effort",
         bg="a frontier general store, shelves of tinned goods and bolts of cloth behind her"),
    dict(slug="wendell_hargrove", name="Wendell Hargrove", faction=VILLAGE,
         desc="a soft-spoken gentle man of about thirty-five, {hargrove}, neatly dressed in a shopkeeper's apron over a clean shirt and tie, a mild slightly anxious face, hands resting carefully on his knees",
         bg="behind the counter of a frontier general store, a brass scale and open ledger beside him"),
    dict(slug="beatrice_hargrove", name="Beatrice Hargrove", faction=VILLAGE,
         desc="a poised composed young woman of about sixteen, {hargrove}, dark hair dressed simply, her mother's bearing without yet her mother's confidence, a neat day dress",
         bg="a frontier general store interior, sunlight through the front window behind her"),
    dict(slug="oliver_hargrove", name="Oliver Hargrove", faction=VILLAGE,
         desc="a gangly boy of about eleven still growing into himself, {hargrove}, dark hair combed flat for the photograph, a ledger open on his knee, unexpectedly serious",
         bg="a general store back office, shelving and stacked crates behind him"),

    # --- Sheriff / Woodworker ----------------------------------------------
    dict(slug="gideon_voss", name="Gideon Voss", faction=VILLAGE,
         desc="a solidly built man of about thirty, calloused hands better suited to fine carving than to a gun belt, a tin star pinned slightly crooked, a guarded closed expression, plain dark shirt and waistcoat",
         bg="a woodworker's shop, half-finished carvings and curled shavings on the bench behind him"),

    # --- Saloon --------------------------------------------------------------
    dict(slug="ruby_vance", name="Ruby Vance", faction=VILLAGE,
         desc="a striking rather than pretty woman of about thirty, {vance}, wild dark hair only half pinned, deep laugh lines, a ready open smile that does not reach tired eyes, a bold patterned dress",
         bg="a frontier saloon, a long bar and shelves of bottles behind her"),
    dict(slug="opal_vance", name="Opal Vance", faction=VILLAGE,
         desc="a sharp-dressed sharper-eyed young woman of about nineteen, {vance}, hair elaborately pinned, a knowing amused set to her mouth, a fitted dress finer than the town can afford",
         bg="a frontier saloon staircase, lamplight and bottles behind her"),
    dict(slug="pearl_vance", name="Pearl Vance", faction=VILLAGE,
         desc="a soft watchful young woman of about sixteen, {vance}, quick to laugh but reading the room, hair loosely pinned, a simple work dress",
         bg="a frontier saloon, tables and upturned chairs behind her"),
    dict(slug="lark_vance", name="Lark Vance", faction=VILLAGE,
         desc="a restless sun-browned teenage girl of about eighteen, {vance}, tall and long-limbed, windblown hair escaping its pins, dust on her boots and hem, a few stray feathers caught on her sleeve, looking as though she would rather be outdoors, a young woman not a small child",
         bg="the back steps of a saloon, open scrubland and vast sky behind her"),
    dict(slug="nell_vance", name="Nell Vance", faction=VILLAGE,
         desc="a wiry teenage girl of about fifteen, {vance}, thoroughly windswept hair, a plain dress with a torn hem, a quick mischievous grin held with difficulty for the exposure, an adolescent not a small child",
         bg="the back steps of a saloon, open scrubland and vast sky behind her"),

    # --- Trapper -------------------------------------------------------------
    dict(slug="wren_halloway", name="Wren Halloway", faction=VILLAGE,
         desc="a lean hard-weathered frontier trapper woman of about twenty-five, wind-burnt sun-cured skin with deep squint lines, short dark hair hacked off roughly at the jaw, sharp pale watchful eyes, an unsmiling guarded expression, filthy scarred hide leathers and a fringed buckskin coat worn through at the elbows, dirt ground into her hands",
         bg="the doorway of a rough trapper's cabin, drying pelts and bundled herbs hanging behind her"),

    # --- The Calders ---------------------------------------------------------
    dict(slug="hiram_calder", name="Hiram Calder", faction=VILLAGE,
         desc="a broad sun-beaten rancher of about thirty-five, {calder}, a face set permanently somewhere between determination and exhaustion, heavy working hands, a rough shirt and canvas trousers",
         bg="a modest dinosaur ranch yard, a rail fence and low barn behind him"),
    dict(slug="della_calder", name="Della Calder", faction=VILLAGE,
         desc="a wiry capable woman of about thirty-five, {calder}, sleeves rolled to the elbow, hands roughened by livestock and kitchen work alike, hair pinned back out of the way, a plain work dress",
         bg="a ranch kitchen doorway, the yard and fence line visible behind her"),
    dict(slug="ezra_calder", name="Ezra Calder", faction=VILLAGE,
         desc="a stooped white-haired elderly man with a pipe clenched in his teeth, deeply creased face, gnarled hands resting on his knees, a battered waistcoat",
         bg="a ranch porch with a chessboard set out on a small table beside him"),
    dict(slug="otis_kline", name="Otis Kline", faction=VILLAGE,
         desc="a stooped white-haired elderly man very like his lifelong friend in age and manner, bushy white whiskers, a shrewd amused squint, a worn jacket",
         bg="a ranch porch with a chessboard set out on a small table beside him"),
    dict(slug="jacob_calder", name="Jacob Calder", faction=VILLAGE,
         desc="a young solidly built ranch hand of about nineteen, {calder}, a fading bruise on one cheekbone, restless coiled energy barely contained for the exposure, a rough open-necked shirt",
         bg="a ranch corral, rail fencing and dust behind him"),
    dict(slug="sarah_calder", name="Sarah Calder", faction=VILLAGE,
         desc="a soft-spoken steady young woman of about eighteen, dark circles beneath her eyes from new motherhood, hair simply pinned, a plain dress, hands quiet in her lap",
         bg="a ranch bedroom doorway, a wooden crib visible behind her"),
    dict(slug="wyatt_calder", name="Wyatt Calder", faction=VILLAGE,
         desc="a six month old infant propped upright in a nest of blankets, round-faced and wide-eyed, one fist at his mouth, fine wispy hair",
         bg="a plain wooden crib with a folded quilt behind him"),
    dict(slug="rosie_calder", name="Rosie Calder", faction=VILLAGE,
         desc="a sun-browned quietly pretty girl of about fifteen, {calder}, a guarded private expression, hair in a simple braid over one shoulder, a plain work dress",
         bg="a ranch fence line at golden hour, open scrubland and wildflowers behind her"),
    dict(slug="tobias_calder", name="Tobias Calder", faction=VILLAGE,
         desc="a scrappy boy of about nine, {calder}, dirt on his face and hands, hair cut badly at home, far more interested in the animals than in holding still",
         bg="a ranch corral gate, rail fencing and dust behind him"),
    dict(slug="mabel_calder", name="Mabel Calder", faction=VILLAGE,
         desc="a small round-faced girl of about four, {calder}, fine flyaway hair, a favourite rag toy trailing from one hand, solemn and slightly overwhelmed",
         bg="a ranch porch step, the yard soft and out of focus behind her"),

    # --- The Sutters ---------------------------------------------------------
    dict(slug="augustus_sutter", name="Augustus Sutter", faction=VILLAGE,
         desc="a broad grey-haired ranch patriarch of about fifty, {sutter}, still physically imposing, the settled authority of an old landowner, a good dark coat and waistcoat",
         bg="the porch of a large established ranch house, deep shade and heavy timber posts behind him"),
    dict(slug="cordelia_sutter", name="Cordelia Sutter", faction=VILLAGE,
         desc="a silver-haired ranch matriarch of about fifty, ramrod straight, a face like carved old leather, absolutely level unsentimental eyes, a plain dark high-necked dress, a scoped rifle resting against the chair beside her",
         bg="the porch of a large established ranch house, open range visible beyond the rail"),
    dict(slug="hattie_sutter", name="Hattie Sutter", faction=VILLAGE,
         desc="a strong-jawed sun-browned young woman of about twenty, {sutter}, dressed for work rather than show in a rough shirt and split riding skirt, a hard intensity in her eyes",
         bg="a large ranch corral, heavy stock fencing and dust behind her"),
    dict(slug="ed_crane", name="Ed Crane", faction=VILLAGE,
         desc="a softer-handed less weathered man of about twenty-three, visibly city-bred despite years on a ranch, neatly trimmed hair, an easy watchful outsider's manner, a town-cut jacket over ranch clothes",
         bg="a large ranch yard, barn doors standing open behind him"),
    dict(slug="wesley_crane", name="Wesley Crane", faction=VILLAGE,
         desc="a fair-haired toddler of about three, unsteady on his feet, clutching the arm of a chair for balance, wide startled eyes at the camera",
         bg="a ranch house parlour, a heavy chair and rug behind him"),
    dict(slug="nora_crane", name="Nora Crane", faction=VILLAGE,
         desc="a bright-eyed curious girl of about six, fair hair loose, entirely unbothered by the camera, a neat pinafore over a work dress",
         bg="a ranch barn doorway, straw and warm shadow behind her"),
    dict(slug="emmett_sutter", name="Emmett Sutter", faction=VILLAGE,
         desc="a heavyset hard-jawed young man of about twenty-two, {sutter}, a face that looks ready for a fight even at rest, thick neck and heavy shoulders, a rough shirt with the collar open",
         bg="a large ranch corral, heavy stock fencing behind him"),
    dict(slug="josie_sutter", name="Josephine Sutter", faction=VILLAGE,
         desc="a delicate-featured but not fragile girl of about fifteen, {sutter}, a careful composed exterior, fair hair neatly dressed, a good day dress",
         bg="a ranch house parlour window, lace curtain and hard daylight behind her"),

    # --- The Pembertons ------------------------------------------------------
    dict(slug="cornelius_pemberton", name="Cornelius Pemberton", faction=VILLAGE,
         desc="a well-dressed deliberately imposing farmer of about forty-five, {pemberton}, silver at the temples, a carefully maintained prosperous appearance, a good waistcoat and watch chain, an expression of settled entitlement",
         bg="a prosperous farm office, a heavy desk and ledgers behind him"),
    dict(slug="prudence_pemberton", name="Prudence Pemberton", faction=VILLAGE,
         desc="an immaculately turned out woman of about forty, {pemberton}, a permanently appraising expression, hair perfectly dressed, a fine dark gown with lace at the throat",
         bg="a formal farmhouse parlour, patterned wallpaper and a mantel clock behind her"),
    dict(slug="walter_pemberton", name="Walter Pemberton", faction=VILLAGE,
         desc="a neat correct young man of about seventeen, {pemberton}, already carrying himself like the landowner he expects to become, hair carefully parted, a good jacket and collar",
         bg="a prosperous farm office doorway, fields visible beyond"),
    dict(slug="louisa_pemberton", name="Louisa Pemberton", faction=VILLAGE,
         desc="a restless girl of about fifteen, {pemberton}, quick sharp eyes taking everything in, hair dressed more plainly than her mother would like, a fine dress worn slightly carelessly",
         bg="a formal farmhouse parlour, a window looking out over fallow fields behind her"),

    # --- The Bandit Company --------------------------------------------------
    dict(slug="barnabas_kane", name="Barnabas Kane", faction=BANDIT,
         desc="a tall powerfully built outlaw leader of about thirty, a heavy square jaw and a hard flat unblinking stare, deliberate theatrical dress, a long trail-worn black duster hanging open, a wide-brimmed black hat with a heavy silver concho band, road dust caked into the leather",
         bg="a bandit camp at dusk, canvas tents and a low fire behind him"),
    dict(slug="thaddeus_marrow", name="Thaddeus Marrow", faction=BANDIT,
         desc="a weathered plainly dressed outlaw lieutenant of about thirty-five, a tired watchful face that has been quietly disagreeing with something for a long time, practical worn clothes without ornament",
         bg="a bandit camp, picketed mounts and supply crates behind him"),
    dict(slug="obadiah_cress", name="Obadiah Cress", faction=BANDIT,
         desc="a heavyset hard-eyed outlaw lieutenant of about thirty, a barely restrained restlessness, a thick neck and heavy hands, a stained coat and a pistol at his belt",
         bg="a bandit camp, canvas tents and hanging tack behind him"),
    dict(slug="prosper_lin", name="Dr. Prosper Lin", faction=BANDIT,
         desc="a precise neatly kept East Asian physician of about thirty-five, wire spectacles, careful clean hands entirely out of place among raiders, a dark coat and waistcoat",
         bg="a bandit camp surgeon's tent, a folding table of instruments behind him"),
    dict(slug="helena_frost", name="Dr. Helena Frost", faction=BANDIT,
         desc="a practical unflinching woman physician of about thirty, sleeves rolled, a calm level bedside expression, hair pinned severely back, a plain apron over travelling clothes",
         bg="a bandit camp surgeon's tent, bandages and bottles behind her"),
    dict(slug="big_sal", name="“Big Sal”", faction=BANDIT,
         desc="an enormous powerfully built woman camp cook of about thirty-five, soot-blackened forearms, a broad open booming laugh, hair tied up in a rag, a scorched apron",
         bg="a bandit camp cook fire, a great iron pot and stacked supplies behind her"),
    dict(slug="whistling_pete", name="“Whistling Pete”", faction=BANDIT,
         desc="a wiry perpetually cheerful camp cook of about thirty, a lopsided grin, lips pursed as though caught mid-whistle, a battered hat pushed back, a filthy apron",
         bg="a bandit camp cook fire, a chuck wagon behind him"),
    dict(slug="dutch_malloy", name="Dutch Malloy", faction=BANDIT,
         desc="a sharp-featured restless-eyed outlaw scout of about twenty-five, the look of someone always half-watching the horizon, a dust-caked neckerchief and a rifle across his knees",
         bg="a high ridge at dusk, open country falling away behind him"),

    # --- Prospectors ---------------------------------------------------------
    dict(slug="ezra_whitlock", name="Ezra Whitlock", faction=NEUTRAL,
         desc="a grizzled sun-cured prospector of about forty-five, a calculating squint, a heavy untrimmed moustache, patched practical gear that has clearly outlasted several better outfits",
         bg="a prospectors' camp among rocks, a canvas lean-to and mining tools behind him"),
    dict(slug="connie_marsh", name="Connie Marsh", faction=NEUTRAL,
         desc="a physically imposing confident woman prospector of about thirty-five, weathered hands that know both a rifle and a fight, hair cropped short and practical, heavy canvas working clothes",
         bg="a prospectors' camp among rocks, a rifle propped against the boulder beside her"),
    dict(slug="yusuf_okafor", name="Yusuf Okafor", faction=NEUTRAL,
         desc="a quiet composed Black prospector of about thirty-five, an economy of movement suggesting old military discipline, close-cropped hair, a neatly kept coat despite the dust",
         bg="a prospectors' camp among rocks, distant plateau country beyond"),

    # --- Miners ---------------------------------------------------------------
    dict(slug="amos_reyes", name="Amos Reyes", faction=NEUTRAL,
         desc="an older cautious-eyed Latino miner of about forty-five, permanently a little hunched from years underground, a face that watches more than it speaks, a dusty coat and battered hat",
         bg="a mine entrance cut into rock, timber props and shadow behind him"),
    dict(slug="zeke_whitcombe", name="Zeke Whitcombe", faction=NEUTRAL,
         desc="a younger animated miner of about twenty-five, soot-marked hands and face, an easy disarming grin, shirtsleeves rolled, a coil of fuse cord over one shoulder",
         bg="a mine entrance cut into rock, ore cart and timber props behind him"),

    # --- Notable deceased ------------------------------------------------------
    dict(slug="barnaby_quist", name="Barnaby Quist", faction=NEUTRAL,
         desc="a big weather-beaten trophy hunter of about forty from an earlier decade, a vast beard and a heavy fur-collared coat, a self-satisfied showman's expression, an old-fashioned long rifle across his knees",
         bg="a formal photographer's studio with a painted canvas backdrop, an older and more formal setup than the rest"),
]


# Dinosaurs get their own framing: a seated waist-up human portrait makes no
# sense for a Diplodocus. `framing` overrides the default per entry.
FULL = "full body in profile, the whole animal within the frame, photographed from a distance"
HEAD = "head and shoulders filling the frame, turned three-quarters toward the camera"
SMALL = "the whole animal close to the camera, perched on a table top or a chair"

DINOSAURS = [
    dict(slug="pip_aquilops", name="Pip", faction=VILLAGE, framing=SMALL,
         desc="a very small horned dinosaur eighteen inches long, a narrow hooked parrot beak, a small bony neck frill behind the skull, four short clawed legs, a thick tapering tail, tight pebbled scaly hide mottled dun and cream, bright alert eyes, tame and entirely unbothered, no feathers, not a bird",
         bg="a blacksmith's workbench, tongs and iron stock behind it"),
    dict(slug="judgment_tyrannosaurus", name="Judgment", faction=BANDIT, framing=FULL,
         desc="an enormous tyrannosaur war mount, deeply scarred hide, a heavy tooled leather riding harness and saddle rig strapped across its shoulders, jaws slightly parted, dark mottled hide with a bony brow ridge",
         bg="a bandit camp at dusk, tents dwarfed beside it and a low fire behind"),
    dict(slug="baryonyx", name="Baryonyx", faction=VILLAGE, framing=FULL,
         desc="a long-snouted crocodile-jawed riding dinosaur, slender and built for distance, a worn hide saddle and pack rig, banded grey-green hide, calm and watchful",
         bg="a shallow river crossing lined with reeds and cottonwoods"),
    dict(slug="carnosaurus", name="Carnosaurus", faction=NEUTRAL, framing=FULL,
         desc="a large trained predatory dinosaur in heavy handling tack, a muzzle strap and chain rig, powerful hind limbs, dark red-brown hide with black striping, controlled but plainly dangerous",
         bg="a heavy timber holding pen on a remote ranch, dust in the air"),
    dict(slug="diplodocus", name="Diplodocus", faction=VILLAGE, framing=FULL,
         desc="an immense sauropod dinosaur ninety feet long, an extremely long slender neck as long as its entire body held out horizontally with a tiny head at the end of it, an even longer whip-like tail trailing far behind, four thick pillar legs, tight elephantine grey hide darkening along the spine, a heavy hauling harness and a timber drag rig, patient and slow",
         bg="a dusty town street, buildings tiny against its flank, the plateau beyond"),
    dict(slug="dryosaurus", name="Dryosaurus", faction=VILLAGE, framing=FULL,
         desc="a slender bipedal dinosaur standing five feet tall at the hip, balanced on two long powerful birdlike hind legs each with three clawed toes, a small narrow beaked head on a short neck, a long stiff tail held straight out behind it, tight pebbled scaly hide in tan with a paler underside, a light riding saddle strapped over its hips, no fur, no hooves, no ears",
         bg="a ranch corral with rail fencing and open scrubland beyond"),
    dict(slug="stegosaurus", name="Stegosaurus", faction=VILLAGE, framing=FULL,
         desc="a heavy four-legged plated dinosaur, a double row of tall bony plates running down its back and four long spikes on its tail, a very small narrow toothless beaked head held low near the ground on a short neck, tiny in proportion to its body, a broad leather draft harness across its shoulders, slow and immensely strong, no teeth, not a predator",
         bg="a ploughed ranch field, a heavy timber cart hitched behind it"),
    dict(slug="triceratops", name="Triceratops", faction=VILLAGE, framing=HEAD,
         desc="a massive three-horned dinosaur with a broad bony neck frill scarred from old fights, small steady eyes, a heavy parrot beak, thick grey-brown hide",
         bg="a ranch gateway, heavy stock fencing behind it"),
    dict(slug="protoceratops", name="Protoceratops", faction=VILLAGE, framing=SMALL,
         desc="a juvenile frilled dinosaur four feet long, a heavy hooked parrot beak, a low bony neck frill behind the skull, a squat four-legged body with clawed reptilian feet and a thick tapering tail, tight pebbled scaly hide mottled sandy grey, sitting placidly indoors like a household pet, no fur, no wool, no floppy ears",
         bg="a country surgery floor, shelves of bottles and a rag rug behind it"),
    dict(slug="micro_raptor", name="Micro-raptor", faction=VILLAGE, framing=SMALL,
         desc="a tiny feathered dromaeosaur dinosaur one foot long, four feathered limbs with long flight feathers on both the arms AND the hind legs, a long stiff banded tail, a toothed reptilian snout, a curved sickle claw on the second toe of each foot, iridescent black plumage, head cocked sharply at the camera, not a crow, not a bird, no beak",
         bg="the back of a wooden chair in a country surgery"),
    dict(slug="pteranodon", name="Pteranodon", faction=VILLAGE, framing=FULL,
         desc="a large crested flying reptile with an enormous wingspan folded at rest, a long backswept bony head crest, a toothless beak, pale leathery wing membranes",
         bg="a high rocky outcrop above open country, vast sky behind it"),
    dict(slug="ankylosaurus", name="Ankylosaurus", faction=NEUTRAL, framing=FULL,
         desc="a squat immensely armoured four-legged dinosaur, its whole back and flanks plated in fused bony knobs and studs, a broad low armoured head, a heavy bony club at the very end of its tail, standing low to the ground on four short thick legs, built like a living barricade, no teeth, not a predator, not standing upright",
         bg="a rocky prospectors' camp, boulders and a canvas lean-to behind it"),
    dict(slug="apatosaurus", name="Apatosaurus", faction=NEUTRAL, framing=FULL,
         desc="a huge sauropod dinosaur seventy feet long, a very long thick neck as long as its whole body held out horizontally, a small blunt head at the end of it, an extremely long tapering tail, four massive pillar legs, dust-caked grey hide, a worn hauling harness, a bad-tempered set to its small head",
         bg="a mine head, ore carts and timber stacks tiny beside it"),
    dict(slug="iguanodon", name="Iguanodon", faction=NEUTRAL, framing=FULL,
         desc="a large plant-eating dinosaur twenty feet long, a long deep snout ending in a toothless cropping beak, a conical spike on each thumb held clear of the ground, four thick columnar legs, a long heavy tail held straight out behind, tight pebbled scaly hide banded olive and grey, no fur, no horns, no ears",
         bg="a remote ranch breeding paddock, dry hills beyond the fence"),
    dict(slug="allosaurus", name="Allosaurus", faction=NEUTRAL, framing=FULL,
         desc="a large wild predatory dinosaur, lean and hungry with prominent brow horns, no harness or tack of any kind, scarred hide, caught mid-stride and staring straight at the camera",
         bg="flooded water meadows at dawn, standing water and reeds, mist low across the ground"),
    dict(slug="utahraptor", name="Utahraptor", faction=BANDIT, framing=FULL,
         desc="a large feathered dromaeosaur dinosaur used as a riding mount, seven feet tall, standing on two legs with a long stiff tail held straight out behind for balance, a toothed reptilian snout full of teeth, an oversized curved sickle claw held raised on the second toe of each foot, barred rust and black plumage over a scaly face, a light raiding saddle and rein rig, poised and alert, not a bird, not an eagle, no beak, no wings",
         bg="a bandit camp picket line, other mounts blurred behind it"),
    dict(slug="therizinosaurus", name="Therizinosaurus", faction=BANDIT, framing=FULL,
         desc="a tall shaggy-feathered dinosaur with grotesquely long scythe-like claws on both arms, a pot-bellied body and a small head, a heavy riding rig across its shoulders, deeply unsettling to look at",
         bg="a bandit camp at dusk, firelight raking across its feathers"),
    dict(slug="deinonychus", name="Deinonychus", faction=NEUTRAL, framing=FULL,
         desc="a wild feathered dromaeosaur dinosaur standing four feet tall on two legs, a toothed reptilian snout, a large curved sickle claw held raised clear of the ground on the second toe of each foot, a long stiff feathered tail held straight out behind, mottled grey-brown plumage, wary and crouched low, no tack of any kind, not a wolf, not a mammal, no fur",
         bg="the ruins of a collapsed frontier fort, broken timber and rubble behind it"),
    dict(slug="kentrosaurus", name="Kentrosaurus", faction=NEUTRAL, framing=FULL,
         desc="a four-legged spiked dinosaur, paired long shoulder spikes and a double row of tall narrow spines down its back and tail, a very small narrow toothless beaked head held low on a short neck, tight scaly hide, bristling and defensive, no teeth, not a predator",
         bg="dry scrub country with scattered boulders"),
    dict(slug="arthropleura", name="Arthropleura", faction=NEUTRAL, framing=FULL,
         desc="an enormous segmented millipede longer than a man, dozens of legs, a glossy dark chitinous shell banded in ochre, low to the ground",
         bg="a damp shaded gully, ferns and rotting timber around it"),
    dict(slug="pulmonoscorpius", name="Pulmonoscorpius", faction=NEUTRAL, framing=FULL,
         desc="a giant scorpion the size of a large dog, heavy pincers raised and its stinger arched high over its back, glossy dark banded carapace",
         bg="a rocky nest hollow strewn with bone fragments and sand"),
]

# Default human framing. Seated is deliberate: standing poses deform hands
# (README, "Two more Klein habits").
DEFAULT_FRAMING = "waist-up, seated squarely facing the camera"

# Batch size is set by kind, not by taste. Humans are seated waist-up with hands
# on knees -- two hands in frame, no feet -- and came back with ZERO anatomical
# artefacts across 59 subjects. Non-humans are full-body: four legs, a tail and
# twenty claws to keep count of, and 10 of 21 came back with an extra, fused or
# detached limb. So creatures get a much bigger batch to cull from.
BATCH_BY_KIND = {"person": 4, "creature": 12}

for _s in CHARACTERS:
    _s.setdefault("kind", "person")
for _s in DINOSAURS:
    _s.setdefault("kind", "creature")

SUBJECTS = CHARACTERS + DINOSAURS


def batch_size(entry):
    """How many candidates to generate for this subject."""
    return BATCH_BY_KIND[entry.get("kind", "person")]


def resolve(entry):
    """Expand the {family} placeholders in a desc."""
    return entry["desc"].format(**FAM)


if __name__ == "__main__":
    from collections import Counter
    print(len(CHARACTERS), "characters +", len(DINOSAURS), "dinosaurs =", len(SUBJECTS), "subjects")
    print(Counter(s["faction"] for s in SUBJECTS))
    slugs = [s["slug"] for s in SUBJECTS]
    assert len(slugs) == len(set(slugs)), "duplicate slug"
    for s in SUBJECTS:
        resolve(s)
        assert s["slug"].replace("_", "").isalnum(), f"unclean slug: {s['slug']}"
    print("all descs resolve, all slugs unique and filename-safe")
