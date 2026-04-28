//character randomisation
const colors = [
"black",
"white",
"silver",
"gray",
"yellow",
"blue",
"sky blue",
"indigo",
"purple",
"red",
"green",
"pink",
"coral",
"brown",
"orange",
"turquoise",
"green",
"aqua",
"amber",
"hazel",
"burgundy",
"vermilion",
"iridescent",
"multicolored",
"two-tone",
"gradient",
"starry print",
]
const hair_length = [
  "very short hair",
  "short hair",
  "medium hair",
  "long hair",
  "very long hair"
]
const hair_addon = [
  "topknot",
  "twintails",
  "low twintails",
  "pixie cut",
  "ponytail",
  "side ponytail",
  "twin ponytails",
  "folded ponytail",
  "side braid",
  "french braid",
  "single braid",
  "twin braids",
  "single hair bun",
  "double bun",
  "braided bun",
  "hair spread out",
  "hair slicked back",
  "hair spiral",
  "bob cut",
  "hime cut",
  "bowl cut",
  "shaggy hair",
  "messy hair",
  "bangs",
  "swept bangs",
  "blunt bangs",
  "crossed bangs",
  "asymmetrical bangs",
  "hair pulled back",
  "covered eyes",
  "hair over eyes, covered eyes, blunt bangs",
  "hair over one eye",
  "hair between eyes"
]
const tops = [
  "__colors__ blouse",
  "__colors__ hoodie",
  "__colors__ vest",
  "__colors__ t-shirt",
  "__colors__ shirt",
  "__colors__ sailor collar, neck ribbon",
  "__colors__ sweater",
  "collared shirt",
  "collared shirt, __colors__ necktie",
  "shirt, bare shoulders",
  "animal hoodie",
  "tube top",
  "camisole",
  "camisole, strap slip",
  "strapless",
  "short sleeves",
  "sleeveless",
  "wide sleeves, frilled shirt",
  "off-shoulder sweater",
  "sweater, {heart|cat} cutout",
  "clothing cutout",
  "{cleavage|underboob|navel} cutout",
  "{hip|shoulder} cutout",
  "{sideboob|underboob|boob window}",
  "{midriff|navel}",
  "necktie",
  "turtleneck",
  "halterneck",
  "crop top",
  "corset",
  "striped shirt, vertical stripes",
  "striped shirt, horizontal stripes",
  "polo shirt",
  "see-through shirt",
  "jacket",
  "track jacket",
  "fur-trimmed jacket",
  "leather jacket",
  "pompom",
  "apron",
  "sports bra",
  "coat",
  "fur coat",
  "cape",
  "capelet",
  "jumper",
  "blazer",
  "poncho"
]
const bottoms = [
  "__colors__ skirt",
  "__colors__ shorts",
  "__colors__ shorts, short shorts",
  "__colors__ pants",
  "__colors__ panties",
  "long skirt",
  "miniskirt",
  "layered skirt",
  "pleated skirt",
  "high-waist skirt",
  "sweatpants",
  "striped pants",
  "hotpants",
  "leather pants",
  "pom-pom pants",
  "jeans",
  "short shorts, thigh strap",
  "denim shorts",
  "bellbottoms"
]

const costumes = [
  "__colors__ dress",
  "__colors__ dress, short dress",
  "__colors__ bikini",
  "__colors__ pajamas",
  "__colors__ kimono",
  "__colors__ tuxedo",
  "frilled dress",
  "strapless dress",
  "off-shoulder dress",
  "china dress",
  "sailor dress",
  "pinafore sress",
  "fur-trimmed dress",
  "armored dress",
  "dress, {sideboob|underboob|boob window}",
  "dress, {clothing|cleavage|underboob|navel|heart|cat} cutout",
  "chinese clothes",
  "japanese clothes",
  "korean clothes",
  "strapless bikini",
  "side-tie bikini",
  "one-piece swimsuit",
  "idol clothes",
  "track suit",
  "bodysuit, latex",
  "maid outfit",
  "nun, habit",
  "nurse",
  "waitress",
  "flight attendant",
  "tuxedo, bowtie",
  "wedding dress",
  "overalls, __colors__ shirt",
  "school uniform",
  "gym uniform",
  "military uniform",
  "armor",
  "japanese armor",
  "toga, greek clothes",
  "pirate costume",
  "santa costume"
]

const accessories = [
  "jewelry",
  "(jewelry)",
  "earrings",
  "heart earrings",
  "star earrings",
  "hoop earrings",
  "(necklace)",
  "(bracelet)",
  "(ring)",
  "jewelry, necklace, bracelet, ring",
  "detached collar",
  "arm strap",
  "leg strap",
  "animal ears",
  "animal ears, tail",
  "animal ears, cat ears",
  "animal ears, cat ears, ear fluff",
  "cat ears",
  "dog ears",
  "wolf ears",
  "fox ears",
  "horse ears",
  "{bunny|rabbit} ears",
  "mouse ears",
  "glasses",
  "sunglasses",
  "round eyewear",
  "tinted eyewear",
  "under-rim eyewear",
  "black-framed eyewear",
  "frills",
  "fishnets",
  "bandages",
  "gold trim",
  "fur trim",
  "lace trim",
  "ribbon trim",
  "__colors__ ribbon",
  "__colors__ bow",
  "__colors__ scarf",
  "__colors__ ribbon, hair ribbon",
  "__colors__ bow, hair bow",
  "__colors__ headwear",
  "hat",
  "headphones",
  "headphones around neck",
  "{baseball cap|backwards cap}",
  "crown",
  "tiara",
  "beret",
  "top hat",
  "helmet",
  "witch hat",
  "halo",
  "hair flower",
  "hair flower, __colors__ flower",
  "hair ornament",
  "x hair ornament",
  "star hair ornament",
  "heart hair ornament",
  "butterfly hair ornament",
  "{cat|food|skull|leaf|feather} hair ornament",
  "gloves",
  "fingerless gloves",
  "elbow gloves",
  "wings",
  "head wings",
  "mini wings",
  "fairy wings",
  "{demon|bat} wings",
  "angel wings, halo",
  "demon horns, demon tail",
  "(mechanical arms, mechanical legs)",
  "face mask",
  "eyepatch",
  "pirate hat"
]


function GetRandom(array) {
  return array[Math.floor(Math.random() * array.length)]
}

export function GetRandomCharacter() {
  var character = `${GetRandom(colors)} hair, ${GetRandom(hair_length)}, ${GetRandom(hair_addon)}, ${GetRandom(colors)} eyes,`

  //30% chance of costume, 70% chance of top and bottom
  if (Math.random() < 0.3) {
    character += ` ${GetRandom(costumes)}`
  } else {
    character += ` ${GetRandom(tops)}, ${GetRandom(bottoms)}`
  }
  //30% chance of no accessories, 70% chance of 1-3 accessories
  if (Math.random() > 0.3) {
    var accessoriesCount = Math.floor(Math.random() * 3) + 1
    for (var i = 0; i < accessoriesCount; i++) {
      character += `, ${GetRandom(accessories)}`
    }
  }

  //replace __colors__ with random colors
  while (character.includes("__colors__")) {
    character = character.replace("__colors__", GetRandom(colors))
  }

  //replace {option1|option2|option3} with random option
  while (character.includes("{")) {
    character = character.replace(/{([^}]+)}/g, function(match, options) {
      var optionsArray = options.split("|")
      return GetRandom(optionsArray)
    })
  }
  return character

}