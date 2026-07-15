<template>
    <!--Clear Art is a artwork with a transparent background-->
    <video v-if="isVideo" :src="url" autoplay loop muted playsinline></video>
    <img v-else :src="url" alt="" />
</template>

<script setup>
import { apiUrl } from '@/api';
import { onMounted, ref, computed } from 'vue';

const props = defineProps({
    animated: {
        type: Boolean,
        default: null
    }
})

const url = ref('')

const isVideo = computed(() => {
    const val = url.value.toLowerCase()
    return val.endsWith('.webm') || val.endsWith('.mp4')
})

const urls = [


    "/files/comfyui/RMBGVID/vid_00001.webm",
    "/files/comfyui/RMBGVID/vid_00002.webm",
    "/files/comfyui/RMBGVID/vid_00003.webm",
    "/files/comfyui/RMBGVID/vid_00004.webm",
    "/files/comfyui/RMBGVID/vid_00005.webm",
    "/files/comfyui/RMBGVID/vid_00006.webm",
    "/files/comfyui/RMBGVID/vid_00006.webm",
    "/files/comfyui/RMBGVID/vid_00007.webm",
    "/files/comfyui/RMBGVID/vid_00008.webm",
    "/files/comfyui/RMBGVID/vid_00009.webm",
    "/files/comfyui/RMBGVID/vid_00010.webm",
    "/files/comfyui/RMBGVID/vid_00011.webm",
    "/files/comfyui/RMBGVID/vid_00012.webm",
    "/files/comfyui/RMBGVID/vid_00013.webm",
    "/files/comfyui/RMBGVID/vid_00014.webm",
    "/files/comfyui/RMBGVID/vid_00015.webm",
    "/files/comfyui/RMBGVID/vid_00016.webm",
    "/files/comfyui/RMBGVID/vid_00017.webm",
    "/files/comfyui/RMBGVID/vid_00018.webm",
    "/files/comfyui/RMBGVID/vid_00019.webm",
    "/files/comfyui/RMBGVID/vid_00020.webm",
    "/files/comfyui/RMBGVID/vid_00021.webm",
    "/files/comfyui/RMBGVID/vid_00022.webm",
    "/files/comfyui/RMBGVID/vid_00023.webm",
    "/files/comfyui/RMBGVID/vid_00024.webm",
    "/files/comfyui/RMBGVID/vid_00025.webm",
    "/files/comfyui/RMBGVID/vid_00026.webm",
    "/files/comfyui/RMBGVID/vid_00027.webm",
    "/files/comfyui/RMBGVID/vid_00028.webm",
    "/files/comfyui/RMBGVID/vid_00029.webm",
    "/files/comfyui/RMBGVID/vid_00030.webm",
    "/files/comfyui/RMBGVID/vid_00031.webm",
    "/files/comfyui/RMBGVID/vid_00032.webm",
    "/files/comfyui/RMBGVID/vid_00033.webm",
    "/files/comfyui/RMBGVID/vid_00034.png",
    "/files/comfyui/RMBGVID/vid_00035.png",




    "https://cdn.donmai.us/original/27/3b/__toutetsu_yuuma_touhou_drawn_by_chups__273bfc163bb1321438cef17f0a88ae6c.png",
    "https://cdn.donmai.us/original/e3/81/__suzakunomiya_karin_taimashi_ayano_drawn_by_kongeraatio__e3812a63bd65aba49d52467347ccea5d.png",
    "https://cdn.donmai.us/original/23/4f/__katsuragi_marina_and_exs_tia_kouyoku_senki_exs_tia_drawn_by_inoino__234f45138b6c40feb2707b63d2793d24.png",
    "https://cdn.donmai.us/original/25/a2/__demon_girl_taimashi_ayano_drawn_by_kongeraatio__25a2256f6a63bc2873a148a5e3703f7c.png",
    "https://cdn.donmai.us/original/1a/1b/__katsuragi_marina_and_exs_tia_kouyoku_senki_exs_tia_drawn_by_inoino__1a1b7bd056c70d05d1260fc7910c39d8.png",
    "https://cdn.donmai.us/original/33/c7/__rokujou_sekka_taimashi_ayano_drawn_by_kongeraatio__33c767d6eb577a1e90559dfc1006e6b1.png",
    "https://cdn.donmai.us/original/23/4e/__ryuujouji_saori_taimashi_ayano_drawn_by_kongeraatio__234e543ecdc7ecc9ed3c3bab2857bdcd.png",
    "https://cdn.donmai.us/original/88/1a/__rokujou_sion_taimashi_ayano_drawn_by_kongeraatio__881a849489c3b125e14a5d5de927e617.png",
    "https://cdn.donmai.us/original/cf/26/__maria_of_penance_last_origin_drawn_by_wow_cor369__cf264d71e442b4a90e5353c773342150.png",
    "https://cdn.donmai.us/original/05/e5/__black_wyrm_last_origin_drawn_by_taesi__05e5bdc33755a7f514b2b416f205a298.png",
    "https://cdn.donmai.us/original/6a/a1/__fotia_of_fireside_last_origin_drawn_by_wow_cor369__6aa170cc41b16a8a1226aba466a49006.png",
    "https://cdn.donmai.us/original/db/a2/__rio_blue_archive_drawn_by_momoriko__dba2b6bdafaaf64106d4e532c07f6587.png",
    "https://cdn.donmai.us/original/e9/6e/__azaz_last_origin_drawn_by_taesi__e96ece84f8296abb9164fe6996797d7c.png",
    "https://cdn.donmai.us/original/00/53/__original_drawn_by_jinggun__0053bd24a06ea974b8d1658494ed2a2d.png",
    "https://cdn.donmai.us/original/42/e3/__melt_last_origin_drawn_by_ren_ren_ko__42e334eca0ec935b8eed302786908f04.png",
    "https://cdn.donmai.us/original/78/93/__hathor_last_origin_drawn_by_taesi__789343f3ca372ce1feb313f3e216b60f.png",
    "https://cdn.donmai.us/original/86/01/__hathor_last_origin_drawn_by_taesi__8601b4491045295d6ace38c53d9136de.png",
    "https://cdn.donmai.us/original/07/12/__hathor_last_origin_drawn_by_taesi__07128f12df55159e6585fcd47b264be9.png",
    "https://cdn.donmai.us/original/11/49/__mihara_goddess_of_victory_nikke_drawn_by_aron_gkdl7554__1149957148a48b7ae669af25b923d384.png",
    "https://cdn.donmai.us/original/68/b7/__quick_camel_last_origin_drawn_by_tunamayo_dsasd751__68b7ca4889fd2d5a5a9ea3f772c46178.png",
    "https://cdn.donmai.us/original/e2/c8/__vivian_oscura_shani_sanjani_septem_percy_klanzeal_and_erza_sarandel_motto_haramase_and_1_more_drawn_by_akagi_rio__e2c84ab3efc265f82dc3658410f36929.webp",
    "https://cdn.donmai.us/original/fe/59/__asuna_blue_archive_drawn_by_tsunamagu__fe5990e3f36ffd5bec7d2b3989b72097.png",
    "https://cdn.donmai.us/original/c8/90/__amyi_sabrina_to_muryoku_na_tamashii_drawn_by_koucha_rakkyo__c890d3fb3ab8f33d42603cb1287edc5d.png",
    "https://cdn.donmai.us/original/67/68/__iowa_and_new_jersey_kantai_collection_and_1_more_drawn_by_jaggi_95__6768916f533e65ec1d22f6dea2eea972.png",
    "https://cdn.donmai.us/original/b1/64/__hina_sabrina_to_muryoku_na_tamashii_drawn_by_koucha_rakkyo__b1641e781b0a0d2e50506c52956670e8.avif",
    "https://cdn.donmai.us/original/ca/f7/__hoshimachi_suisei_hololive_drawn_by_fawny__caf70eaf4653988157f73acab66b5f79.png",
    "https://cdn.donmai.us/original/7c/28/__st_louis_azur_lane_drawn_by_yunsang__7c28804b036d3cf9d9e860167f2e88f6.png",
    "https://cdn.donmai.us/original/f9/20/__mononobe_no_futo_touhou_drawn_by_chiroshiron__f920fc6d33ed993c8ad5156a1d50a69b.png",
    "https://cdn.donmai.us/original/ad/39/__bloody_panther_last_origin_drawn_by_taesi__ad3939396016839ba9911a001b07479a.png",
    "https://cdn.donmai.us/original/cf/26/__maria_of_penance_last_origin_drawn_by_wow_cor369__cf264d71e442b4a90e5353c773342150.png",
    "https://cdn.donmai.us/original/e6/91/__black_lilith_last_origin_drawn_by_kakiman__e6918be6be027b2ffce3dd9b90770225.png",
    "https://cdn.donmai.us/original/32/65/3265307c17891f7e4bc2ab275a301011.webm",
    "https://cdn.donmai.us/original/d6/b1/__kunoichi_kaen_last_origin_drawn_by_c_honey__d6b1af9db800ce68ee1f5d9cf5658f1e.png",
    "https://cdn.donmai.us/original/8b/a0/__robetta_reverie_drawn_by_itinana__8ba0701743333d6014c02694c326733f.webp",
    "https://cdn.donmai.us/original/0f/d4/__yae_miko_yae_sakura_and_sakura_ayane_genshin_impact_and_3_more_drawn_by_vale_x__0fd4701968e2104423f0a89d62496ef7.png",
    "https://cdn.donmai.us/original/7b/e4/__rokujou_sion_taimashi_ayano_drawn_by_kongeraatio__7be4e0d589be4c313e5c2644bad9bec5.png",
    "https://cdn.donmai.us/original/47/42/__exosister_irene_yu_gi_oh_drawn_by_wepwawet__47422ecd0df485fc023c56ef3461c388.png",
    "https://cdn.donmai.us/original/ed/25/__elira_pendora_nijisanji_and_1_more_drawn_by_supahboodge__ed255e47f1e5b0d1f4da3d5a0d9370c5.png",
    "https://cdn.donmai.us/original/1d/2f/__philo_and_rusha_forestia_chiisana_machi_no_bokujou_life_drawn_by_sakana_no_ike__1d2f3900eb7cd3c4bda7a67b6a9293a2.webp",
    "https://cdn.donmai.us/original/62/be/__rose_liz_to_rose_no_koubou_shakkin_shimai_no_koubou_nisshi_drawn_by_wakuta_chisaki__62be3f8745d35ff4394dfc888410c8f6.avif",
    "https://cdn.donmai.us/original/a3/ed/__enjou_sakuya_original_and_1_more_drawn_by_rindou_radical_dream__a3ed8be56fcf0685c117ca754fb4d7dd.png",
    "https://cdn.donmai.us/original/72/e0/__enjou_sakuya_original_and_1_more_drawn_by_rindou_radical_dream__72e06674a61392916ebaf258c1b24e6b.png",
    "https://cdn.donmai.us/original/5a/9e/__yamada_maya_infinite_stratos_drawn_by_kiyama_satoshi__5a9e34d3530ef3599e35948667f2fa15.png",
    "https://cdn.donmai.us/original/b2/f3/__yamada_maya_infinite_stratos_drawn_by_kiyama_satoshi__b2f32f6e71a5cb381ff781382f067edb.png",
    "https://cdn.donmai.us/original/2e/48/__lemonade_epsilon_last_origin_drawn_by_ren_ren_ko__2e488202e4216b3b319307082eeab296.png",
    "https://cdn.donmai.us/original/68/e1/__nakano_nino_go_toubun_no_hanayome_drawn_by_kouzuki_majc8345__68e1c36db24792052501e890e98d6252.png",
    "https://cdn.donmai.us/original/a6/6a/__shiro_hikari_to_kage_no_doppelganger_drawn_by_geocentrism_theory__a66a2cabaa360ee813faccdcb070ff20.png",
    "https://cdn.donmai.us/original/bf/62/__mp40_girls_frontline_drawn_by_nekobao__bf62e6b940cdc09fd8efc69108fc2d39.png",
    "https://cdn.donmai.us/original/cf/1f/__uzaki_tsuki_uzaki_chan_wa_asobitai_drawn_by_namidame__cf1fa620558dabea1559ad92eae05028.png",
    "https://cdn.donmai.us/original/1f/24/__durandal_honkai_and_1_more_drawn_by_lrh0123__1f24eedbcccca0abbc01b3fb302bffc7.png",
    "https://cdn.donmai.us/original/fb/1c/__palmier_selam_and_charlotte_boku_ga_incubus_ni_naru_tame_ni_kyou_kara_succubus_to_lesson_shimasu_drawn_by_shiokonbu__fb1c445f6cf635315cfa6a9f1c6bedf1.png",
    "https://cdn.donmai.us/original/85/c0/__isekai_harem_fantasia_drawn_by_kaisen_chuui__85c003fda97223277fa98694e187f6b6.png",
    "https://cdn.donmai.us/original/25/da/__renoa_chaos_zero_nightmare_drawn_by_leovic_and_rimutsutaka__25da19e885919c823ad7f8510113f6db.png",
    "https://cdn.donmai.us/original/af/1c/__asuna_blue_archive_drawn_by_lucknight__af1caa87c189fe60a5352faafb5d2d3c.png",
    "https://cdn.donmai.us/original/ae/8f/__original_drawn_by_little_egg__ae8f52097b9c5b16249546053ed2abee.png",
    "https://cdn.donmai.us/original/8d/fe/__jeanne_d_arc_alter_fate_and_1_more_drawn_by_wantsupanchi__8dfe895852e10ffae855d211ee948377.png",
    "https://cdn.donmai.us/original/3a/f9/__emily_last_origin_drawn_by_pelican_s030__3af95ab60341c65436c4709ad5d8d521.png",
    "https://cdn.donmai.us/original/0c/ee/__shizuku_azur_lane_and_2_more__0ceee9d310ccb6007a7c10d926d06b89.png",
    "https://cdn.donmai.us/original/63/59/__raora_panthera_hololive_and_1_more_drawn_by_minhart__6359a55b40988114199a2a6cb6e6506b.gif",
    "https://cdn.donmai.us/original/4f/85/__ilulu_kobayashi_san_chi_no_maidragon_drawn_by_sonao__4f85750d309e1ef0c04b5c1a793e89b7.gif",
    "https://cdn.donmai.us/original/72/47/7247a55d2f0eaea522d4509a29009ec0.webm",
    "https://cdn.donmai.us/original/24/c2/24c2f8d54fe867c4883f8ab919859fdf.webm",
    "https://cdn.donmai.us/original/62/73/6273defa5774b263b3c3b632a8024c67.webm",
    "https://cdn.donmai.us/original/c9/2f/__komi_shouko_komi_san_wa_komyushou_desu_drawn_by_mike_inel__c92fad631f6bb90cfc51109fc70308a2.gif",
    "https://cdn.donmai.us/original/3a/c6/3ac677163067574ee60fad56f01d14c2.webm",
    "https://cdn.donmai.us/original/5e/3d/5e3d668ed2ab671fc700d648dd28c321.webm",
    "https://cdn.donmai.us/original/4c/14/4c140b33872fa9d6481ccb94fac3fdad.webm",
    "https://cdn.donmai.us/original/96/97/969781d4fab7c5a760f787ab9d5f9ccd.webm",
    "https://cdn.donmai.us/original/4e/e1/4ee15ff12e05f12bc85ddefac1ff220f.webm",
    "https://cdn.donmai.us/original/d2/df/d2df9bebe4d6559546f34197b101580f.webm",
    "https://cdn.donmai.us/original/d8/fa/d8fabde4a6414d192ad0f8e0434a3e0e.webm",
    "https://cdn.donmai.us/original/e8/51/e851ab0c23cd1149668ad14fa3c3ce48.webm",
    "https://cdn.donmai.us/original/6a/a7/6aa73969aa8b684277610ec74a251080.webm",
    "https://cdn.donmai.us/original/16/be/16be671c9a775fb15fc993f8ab3b4da8.webm",
    "https://cdn.donmai.us/original/4f/c2/4fc2462921819f882f63c07d2f5c0491.webm",
    "https://cdn.donmai.us/original/01/c1/01c1a96c87ebf3d45f3d02f962468921.webm",
    "https://cdn.donmai.us/original/3c/6f/3c6f9e98423d1af35cf486bee46dafbb.webm",
    "https://cdn.donmai.us/original/72/0e/720e6387fc154ef3df3028e0c8b7fb90.webm",
    "https://cdn.donmai.us/original/eb/ca/ebca981df1e56f6dc6c001c435293de4.webm",
    "https://cdn.donmai.us/original/97/4b/974b070066e59995d7f7cf786eabaa03.webm",
    "https://cdn.donmai.us/original/b1/d1/b1d1d189acabd04f54db7011fa784d09.webm",
    "https://cdn.donmai.us/original/4d/55/4d55c7e216cca68acc398f02717a84ee.webm",
    "https://cdn.donmai.us/original/a5/e5/a5e5f98640fec3543518a44891fff87a.webm",
    "https://cdn.donmai.us/original/f2/6a/f26a2911e1dd8daa5ded1e10d70f41cf.webm",
    "https://cdn.donmai.us/original/c2/ab/c2ab78eb42784296f057cda03252d893.webm",
    "https://cdn.donmai.us/original/6e/5d/6e5d7232816db84ab74c1005fb58ae7b.webm",
    "https://cdn.donmai.us/original/39/f1/39f1283670db007a34205d6b2f65c39d.webm",
    "https://cdn.donmai.us/original/4b/37/4b376a8e22a6a7e83bfaa812eaf65446.webm",
    "https://cdn.donmai.us/original/92/3d/923dc44d44f2c38765c26abc322ffbbd.webm",
    "https://cdn.donmai.us/original/f8/36/f836688265048120500ed526013a5bff.webm",
    "https://cdn.donmai.us/original/78/b3/78b3ded0603ecb6b63eee2f4edd65851.webm",
    "https://cdn.donmai.us/original/65/5f/655f31114b07572a88b6d392db9afbe6.webm",
    "https://cdn.donmai.us/original/8e/55/8e55354c3e77927f51eb05f83595d413.webm",
    "https://cdn.donmai.us/original/b6/be/b6be1de6e093b6c10febc2972a9529a6.webm",
    "https://cdn.donmai.us/original/f6/95/f695d4e1b5b51ff7e7f0fe4ceb382a0b.webm",
    "https://cdn.donmai.us/original/db/19/db1969e955dfa7bd7a4aa734e5adcb90.webm",
    "https://cdn.donmai.us/original/c4/42/c4423a810ed861c387d0d5e7b4f90de9.webm",
    "https://cdn.donmai.us/original/5b/42/5b4209dac5e829e1b5d822543dfe20ea.webm",
    "https://cdn.donmai.us/original/a9/94/a99431d745b3f49be8aa69956dd25a9f.webm",
    "https://cdn.donmai.us/original/e0/16/__mabel_pines_gravity_falls_drawn_by_mike_inel__e01680caec1279862ad1aba5f1d398a9.gif",
    "https://cdn.donmai.us/original/54/27/54279b68ddb511b9d3cbb94a3449faeb.webm",
    "https://cdn.donmai.us/original/be/c7/bec7fe90260525bb9c5c58f3dae2836b.webm",
    "https://cdn.donmai.us/original/8b/e8/8be827934660d44ab8220fca2c61a641.webm",
    "https://cdn.donmai.us/original/e9/94/e9948caeb329de11c857c1452d8cb373.webm",
    "https://cdn.donmai.us/original/b4/36/b436e44fc3c6b2326de59d6c3612e492.webm",
    "https://cdn.donmai.us/original/54/a3/54a3ec5ebdba5f47736ccd9f19b409d9.webm",
    "https://wimg.rule34.xxx//images/4742/82e9208daddc3137ea643300385e04b6.gif",
    "https://wimg.rule34.xxx//images/2877/a742fdd41d734263bbda3673cf5146b8.gif",
    "https://wimg.rule34.xxx//images/1639/06f986ba4ef1e450502d9cb9a0db7299.gif",
    "https://wimg.rule34.xxx//images/4863/3c8d1b421e107fcb2fb356f5dc5ba0e2.gif",
    "https://wimg.rule34.xxx//images/2645/1ed9158c4f14a249e2884d595a7c0bde.gif",
    "https://wimg.rule34.xxx//images/920/729a779b3a0efffee7f91a699b558dbb66a8e234.gif",
    "https://wimg.rule34.xxx//images/2470/f196a8a3b2f5f11189132f59029d8640.gif",
    "https://wimg.rule34.xxx//images/1023/583677c5d5b2b1f9d16321b33b0c39f9.gif",
    "https://wimg.rule34.xxx//images/2735/3c50885ca392f5d03a4467f575cd3ba7.gif",
    "https://wimg.rule34.xxx//images/585/005df4eab3591fe436aca4b6ba1d64c0.gif",

]

function isAnimatedUrl(targetUrl) {
    const val = targetUrl.toLowerCase()
    return val.endsWith('.gif') || val.endsWith('.webm') || val.endsWith('.mp4')
}

onMounted(() => {
    let filteredUrls = urls
    if (props.animated === true) {
        filteredUrls = urls.filter(u => isAnimatedUrl(u))
    } else if (props.animated === false) {
        filteredUrls = urls.filter(u => !isAnimatedUrl(u))
    }

    if (filteredUrls.length === 0) {
        filteredUrls = urls
    }

    let _url = filteredUrls[Math.floor(Math.random() * filteredUrls.length)]

    if (_url.startsWith("/")) {
        url.value = `${apiUrl}${_url}`
    } else {
        url.value = _url
    }
})
</script>
