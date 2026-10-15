struct positions_buffer {
    member: array<f32>,
}

struct radius_buffer {
    member: array<f32>,
}

struct joint_i_buffer {
    member: array<u32>,
}

struct joint_f_buffer {
    member: array<f32>,
}

struct solve_joints_push {
    first: u32,
    count: u32,
}

struct chunk_obj_count_buffer {
    member: array<u32>,
}

struct collision_cells_buffer {
    member: array<u32>,
}

struct cell_ids_buffer {
    member: array<u32>,
}

struct object_ids_buffer {
    member: array<u32>,
}

struct uniform_data_buffer {
    member: array<u32>,
}

struct groups_buffer {
    member: array<u32>,
}

struct solve_collisions_grouped_push {
    current_cell_color: u32,
}

struct previous_positions_buffer {
    member: array<f32>,
}

struct tags_buffer {
    member: array<u32>,
}

struct integrate_tagged_push {
    delta_time: f32,
    gravity_x: f32,
    gravity_y: f32,
    damping: f32,
    sand_damping: f32,
    world_width: f32,
    world_height: f32,
    num_particles: u32,
}

struct tiles_buffer {
    member: array<u32>,
}

struct tile_friction_push {
    tiles_w: u32,
    tiles_h: u32,
    num_particles: u32,
    mu: f32,
    absorb: f32,
}

struct rays_buffer {
    member: array<f32>,
}

struct hits_buffer {
    member: array<f32>,
}

struct hit_ids_buffer {
    member: array<u32>,
}

struct raycast_push {
    tiles_w: u32,
    tiles_h: u32,
    num_circles: u32,
    num_rays: u32,
    mask: u32,
    ignore_group: u32,
}

struct sensors_buffer {
    member: array<f32>,
}

struct sensor_mask_buffer {
    member: array<u32>,
}

struct sensor_counts_buffer {
    member: array<u32>,
}

struct sensor_count_push {
    num_circles: u32,
    num_sensors: u32,
}

struct sensor_counts_buffer_1 {
    member: array<atomic<u32>>,
}

@group(0) @binding(0) 
var<storage, read_write> positions: positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius: radius_buffer;
@group(0) @binding(6) 
var<storage, read_write> joint_i: joint_i_buffer;
@group(0) @binding(7) 
var<storage, read_write> joint_f: joint_f_buffer;
@group(0) @binding(30) 
var<uniform> solve_joints_args: solve_joints_push;
var<private> gl_GlobalInvocationId_6: vec3<u32>;
@group(0) @binding(0) 
var<storage, read_write> chunk_obj_count: chunk_obj_count_buffer;
@group(0) @binding(1) 
var<storage, read_write> collision_cells: collision_cells_buffer;
@group(0) @binding(2) 
var<storage, read_write> cell_ids: cell_ids_buffer;
@group(0) @binding(3) 
var<storage, read_write> object_ids: object_ids_buffer;
@group(0) @binding(4) 
var<storage, read_write> positions_1: positions_buffer;
@group(0) @binding(5) 
var<storage, read_write> radius_1: radius_buffer;
@group(0) @binding(6) 
var<storage, read_write> uniform_data: uniform_data_buffer;
@group(0) @binding(7) 
var<storage, read_write> groups: groups_buffer;
@group(0) @binding(30) 
var<uniform> solve_collisions_grouped_args: solve_collisions_grouped_push;
@group(0) @binding(0) 
var<storage, read_write> positions_2: positions_buffer;
@group(0) @binding(1) 
var<storage, read_write> previous_positions: previous_positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius_2: radius_buffer;
@group(0) @binding(3) 
var<storage, read_write> tags: tags_buffer;
@group(0) @binding(30) 
var<uniform> integrate_tagged_args: integrate_tagged_push;
@group(0) @binding(0) 
var<storage, read_write> positions_3: positions_buffer;
@group(0) @binding(1) 
var<storage, read_write> previous_positions_1: previous_positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius_3: radius_buffer;
@group(0) @binding(5) 
var<storage, read_write> tiles: tiles_buffer;
@group(0) @binding(30) 
var<uniform> tile_friction_args: tile_friction_push;
@group(0) @binding(0) 
var<storage, read_write> positions_4: positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius_4: radius_buffer;
@group(0) @binding(3) 
var<storage, read_write> groups_1: groups_buffer;
@group(0) @binding(5) 
var<storage, read_write> tiles_1: tiles_buffer;
@group(0) @binding(8) 
var<storage, read_write> rays: rays_buffer;
@group(0) @binding(9) 
var<storage, read_write> hits: hits_buffer;
@group(0) @binding(10) 
var<storage, read_write> hit_ids: hit_ids_buffer;
@group(0) @binding(30) 
var<uniform> raycast_args: raycast_push;
@group(0) @binding(0) 
var<storage, read_write> positions_5: positions_buffer;
@group(0) @binding(2) 
var<storage, read_write> radius_5: radius_buffer;
@group(0) @binding(4) 
var<storage, read_write> tags_1: tags_buffer;
@group(0) @binding(11) 
var<storage, read_write> sensors: sensors_buffer;
@group(0) @binding(12) 
var<storage, read_write> sensor_mask: sensor_mask_buffer;
@group(0) @binding(13) 
var<storage, read_write> sensor_counts: sensor_counts_buffer_1;
@group(0) @binding(30) 
var<uniform> sensor_count_args: sensor_count_push;

fn solve_joints_1() {
    var local: u32;
    var local_1: u32;
    var local_2: u32;
    var local_3: u32;
    var local_4: u32;
    var local_5: u32;
    var local_6: u32;
    var local_7: u32;
    var local_8: u32;
    var local_9: u32;
    var local_10: u32;
    var local_11: u32;
    var local_12: u32;
    var local_13: u32;
    var local_14: u32;
    var local_15: u32;
    var local_16: u32;
    var local_17: u32;
    var local_18: u32;
    var local_19: u32;
    var local_20: u32;
    var local_21: u32;
    var local_22: u32;
    var local_23: u32;
    var local_24: u32;
    var local_25: u32;
    var local_26: u32;
    var local_27: u32;
    var local_28: u32;
    var local_29: u32;
    var local_30: u32;
    var local_31: u32;
    var local_32: u32;
    var local_33: f32;
    var local_34: f32;
    var local_35: u32;
    var local_36: u32;
    var local_37: u32;
    var local_38: u32;
    var local_39: f32;
    var local_40: f32;
    var local_41: u32;
    var local_42: u32;
    var local_43: u32;
    var local_44: u32;
    var local_45: u32;
    var local_46: f32;
    var local_47: f32;
    var local_48: u32;
    var local_49: u32;
    var local_50: u32;
    var local_51: u32;
    var local_52: u32;
    var local_53: u32;
    var local_54: f32;
    var local_55: f32;
    var local_56: u32;
    var local_57: u32;
    var local_58: u32;
    var local_59: u32;
    var local_60: f32;
    var local_61: f32;
    var local_62: f32;
    var local_63: u32;
    var local_64: u32;
    var local_65: u32;
    var local_66: u32;
    var local_67: f32;
    var local_68: f32;
    var local_69: u32;
    var local_70: u32;
    var local_71: u32;
    var local_72: u32;
    var local_73: f32;
    var local_74: f32;
    var local_75: f32;
    var local_76: u32;
    var local_77: u32;
    var local_78: u32;
    var local_79: u32;
    var local_80: u32;
    var local_81: u32;
    var local_82: f32;
    var local_83: u32;
    var local_84: u32;
    var local_85: u32;
    var local_86: u32;
    var local_87: u32;
    var local_88: u32;
    var local_89: f32;
    var local_90: u32;
    var local_91: u32;
    var local_92: u32;
    var local_93: u32;
    var local_94: f32;
    var local_95: f32;
    var local_96: f32;
    var local_97: f32;
    var local_98: f32;
    var local_99: f32;
    var local_100: f32;
    var local_101: f32;
    var local_102: f32;
    var local_103: f32;
    var local_104: f32;
    var local_105: f32;
    var local_106: u32;
    var local_107: f32;
    var local_108: f32;
    var local_109: u32;
    var local_110: u32;
    var local_111: u32;
    var local_112: u32;
    var local_113: u32;
    var local_114: u32;
    var local_115: u32;
    var local_116: u32;
    var local_117: f32;
    var local_118: f32;
    var local_119: f32;
    var local_120: f32;
    var local_121: f32;
    var local_122: f32;
    var local_123: f32;
    var local_124: f32;
    var local_125: f32;
    var local_126: f32;
    var local_127: f32;
    var local_128: u32;
    var local_129: u32;
    var local_130: u32;
    var local_131: u32;
    var local_132: u32;
    var local_133: f32;
    var local_134: f32;
    var local_135: f32;
    var local_136: u32;
    var local_137: u32;
    var local_138: u32;
    var local_139: u32;
    var local_140: u32;
    var local_141: u32;
    var local_142: u32;
    var local_143: f32;
    var local_144: f32;
    var local_145: f32;
    var local_146: u32;
    var local_147: u32;
    var local_148: u32;
    var local_149: u32;
    var local_150: u32;
    var local_151: f32;
    var local_152: f32;
    var local_153: f32;
    var local_154: u32;
    var local_155: u32;
    var local_156: u32;
    var local_157: u32;
    var local_158: u32;
    var local_159: u32;

    local = 0u;
    local_1 = 0u;
    local_2 = 0u;
    local_3 = 0u;
    let _e229 = solve_joints_args.first;
    local_4 = _e229;
    let _e231 = solve_joints_args.count;
    local_5 = _e231;
    let _e233 = gl_GlobalInvocationId_6[0u];
    local_6 = _e233;
    let _e234 = local_6;
    local_7 = _e234;
    let _e235 = local_7;
    let _e236 = local_5;
    local_8 = select(0u, 1u, (_e235 >= _e236));
    let _e239 = local_8;
    if (_e239 == 0u) {
    } else {
        return;
    }
    let _e241 = local_4;
    let _e242 = local_7;
    local_9 = (_e241 + _e242);
    let _e244 = local_9;
    local_10 = (_e244 * 4u);
    let _e246 = local_10;
    local_11 = _e246;
    let _e247 = local_11;
    local_12 = _e247;
    let _e248 = local_12;
    local_13 = _e248;
    let _e249 = local_13;
    local_14 = (_e249 * 4u);
    let _e251 = local_2;
    let _e252 = local_14;
    local_15 = (_e251 + _e252);
    let _e254 = local_15;
    let _e259 = joint_i.member[(_e254 >> bitcast<u32>(2u))];
    local_16 = _e259;
    let _e260 = local_16;
    local_17 = _e260;
    let _e261 = local_12;
    local_18 = (_e261 + 1u);
    let _e263 = local_18;
    local_19 = _e263;
    let _e264 = local_19;
    local_20 = (_e264 * 4u);
    let _e266 = local_2;
    let _e267 = local_20;
    local_21 = (_e266 + _e267);
    let _e269 = local_21;
    let _e274 = joint_i.member[(_e269 >> bitcast<u32>(2u))];
    local_22 = _e274;
    let _e275 = local_22;
    local_23 = _e275;
    let _e276 = local_12;
    local_24 = (_e276 + 2u);
    let _e278 = local_24;
    local_25 = _e278;
    let _e279 = local_25;
    local_26 = (_e279 * 4u);
    let _e281 = local_2;
    let _e282 = local_26;
    local_27 = (_e281 + _e282);
    let _e284 = local_27;
    let _e289 = joint_i.member[(_e284 >> bitcast<u32>(2u))];
    local_28 = _e289;
    let _e290 = local_28;
    local_29 = _e290;
    let _e291 = local_12;
    local_30 = _e291;
    let _e292 = local_30;
    local_31 = (_e292 * 4u);
    let _e294 = local_3;
    let _e295 = local_31;
    local_32 = (_e294 + _e295);
    let _e297 = local_32;
    let _e302 = joint_f.member[(_e297 >> bitcast<u32>(2u))];
    local_33 = _e302;
    let _e303 = local_33;
    local_34 = _e303;
    let _e304 = local_12;
    local_35 = (_e304 + 1u);
    let _e306 = local_35;
    local_36 = _e306;
    let _e307 = local_36;
    local_37 = (_e307 * 4u);
    let _e309 = local_3;
    let _e310 = local_37;
    local_38 = (_e309 + _e310);
    let _e312 = local_38;
    let _e317 = joint_f.member[(_e312 >> bitcast<u32>(2u))];
    local_39 = _e317;
    let _e318 = local_39;
    local_40 = _e318;
    let _e319 = local_17;
    local_41 = (_e319 * 2u);
    let _e321 = local_41;
    local_42 = _e321;
    let _e322 = local_42;
    local_43 = _e322;
    let _e323 = local_43;
    local_44 = (_e323 * 4u);
    let _e325 = local;
    let _e326 = local_44;
    local_45 = (_e325 + _e326);
    let _e328 = local_45;
    let _e333 = positions.member[(_e328 >> bitcast<u32>(2u))];
    local_46 = _e333;
    let _e334 = local_46;
    local_47 = _e334;
    let _e335 = local_17;
    local_48 = (_e335 * 2u);
    let _e337 = local_48;
    local_49 = (_e337 + 1u);
    let _e339 = local_49;
    local_50 = _e339;
    let _e340 = local_50;
    local_51 = _e340;
    let _e341 = local_51;
    local_52 = (_e341 * 4u);
    let _e343 = local;
    let _e344 = local_52;
    local_53 = (_e343 + _e344);
    let _e346 = local_53;
    let _e351 = positions.member[(_e346 >> bitcast<u32>(2u))];
    local_54 = _e351;
    let _e352 = local_54;
    local_55 = _e352;
    let _e353 = local_17;
    local_56 = _e353;
    let _e354 = local_56;
    local_57 = _e354;
    let _e355 = local_57;
    local_58 = (_e355 * 4u);
    let _e357 = local_1;
    let _e358 = local_58;
    local_59 = (_e357 + _e358);
    let _e360 = local_59;
    let _e365 = radius.member[(_e360 >> bitcast<u32>(2u))];
    local_60 = _e365;
    let _e366 = local_60;
    local_61 = (1f / _e366);
    let _e368 = local_61;
    local_62 = _e368;
    let _e369 = local_12;
    local_63 = (_e369 + 2u);
    let _e371 = local_63;
    local_64 = _e371;
    let _e372 = local_64;
    local_65 = (_e372 * 4u);
    let _e374 = local_3;
    let _e375 = local_65;
    local_66 = (_e374 + _e375);
    let _e377 = local_66;
    let _e382 = joint_f.member[(_e377 >> bitcast<u32>(2u))];
    local_67 = _e382;
    let _e383 = local_67;
    local_68 = _e383;
    let _e384 = local_12;
    local_69 = (_e384 + 3u);
    let _e386 = local_69;
    local_70 = _e386;
    let _e387 = local_70;
    local_71 = (_e387 * 4u);
    let _e389 = local_3;
    let _e390 = local_71;
    local_72 = (_e389 + _e390);
    let _e392 = local_72;
    let _e397 = joint_f.member[(_e392 >> bitcast<u32>(2u))];
    local_73 = _e397;
    let _e398 = local_73;
    local_74 = _e398;
    local_75 = 0f;
    let _e399 = local_23;
    local_76 = select(0u, 1u, (_e399 != 4294967295u));
    let _e402 = local_76;
    if (_e402 == 0u) {
    } else {
        let _e404 = local_23;
        local_77 = (_e404 * 2u);
        let _e406 = local_77;
        local_78 = _e406;
        let _e407 = local_78;
        local_79 = _e407;
        let _e408 = local_79;
        local_80 = (_e408 * 4u);
        let _e410 = local;
        let _e411 = local_80;
        local_81 = (_e410 + _e411);
        let _e413 = local_81;
        let _e418 = positions.member[(_e413 >> bitcast<u32>(2u))];
        local_82 = _e418;
        let _e419 = local_82;
        local_68 = _e419;
        let _e420 = local_23;
        local_83 = (_e420 * 2u);
        let _e422 = local_83;
        local_84 = (_e422 + 1u);
        let _e424 = local_84;
        local_85 = _e424;
        let _e425 = local_85;
        local_86 = _e425;
        let _e426 = local_86;
        local_87 = (_e426 * 4u);
        let _e428 = local;
        let _e429 = local_87;
        local_88 = (_e428 + _e429);
        let _e431 = local_88;
        let _e436 = positions.member[(_e431 >> bitcast<u32>(2u))];
        local_89 = _e436;
        let _e437 = local_89;
        local_74 = _e437;
        let _e438 = local_23;
        local_90 = _e438;
        let _e439 = local_90;
        local_91 = _e439;
        let _e440 = local_91;
        local_92 = (_e440 * 4u);
        let _e442 = local_1;
        let _e443 = local_92;
        local_93 = (_e442 + _e443);
        let _e445 = local_93;
        let _e450 = radius.member[(_e445 >> bitcast<u32>(2u))];
        local_94 = _e450;
        let _e451 = local_94;
        local_95 = (1f / _e451);
        let _e453 = local_95;
        local_75 = _e453;
    }
    let _e454 = local_68;
    let _e455 = local_47;
    local_96 = (_e454 - _e455);
    let _e457 = local_96;
    local_97 = _e457;
    let _e458 = local_74;
    let _e459 = local_55;
    local_98 = (_e458 - _e459);
    let _e461 = local_98;
    local_99 = _e461;
    let _e462 = local_97;
    let _e463 = local_97;
    local_100 = (_e462 * _e463);
    let _e465 = local_99;
    let _e466 = local_99;
    local_101 = (_e465 * _e466);
    let _e468 = local_100;
    let _e469 = local_101;
    local_102 = (_e468 + _e469);
    let _e471 = local_102;
    local_103 = sqrt(_e471);
    let _e473 = local_103;
    local_104 = _e473;
    local_105 = 0.0001f;
    let _e474 = local_104;
    let _e475 = local_105;
    local_106 = select(0u, 1u, (_e474 < _e475));
    let _e478 = local_106;
    if (_e478 == 0u) {
    } else {
        return;
    }
    let _e480 = local_104;
    let _e481 = local_34;
    local_107 = (_e480 - _e481);
    let _e483 = local_107;
    local_108 = _e483;
    let _e484 = local_29;
    local_109 = (_e484 & 1u);
    let _e486 = local_109;
    local_110 = select(0u, 1u, (_e486 != 0u));
    local_111 = 1u;
    let _e489 = local_110;
    if (_e489 == 0u) {
        local_111 = 0u;
    } else {
        let _e491 = local_108;
        local_112 = select(0u, 1u, (_e491 < 0f));
        let _e494 = local_112;
        if (_e494 == 0u) {
            local_111 = 0u;
        }
    }
    let _e496 = local_111;
    if (_e496 == 0u) {
    } else {
        return;
    }
    let _e498 = local_29;
    local_113 = (_e498 & 2u);
    let _e500 = local_113;
    local_114 = select(0u, 1u, (_e500 != 0u));
    local_115 = 1u;
    let _e503 = local_114;
    if (_e503 == 0u) {
        local_115 = 0u;
    } else {
        let _e505 = local_108;
        local_116 = select(0u, 1u, (_e505 > 0f));
        let _e508 = local_116;
        if (_e508 == 0u) {
            local_115 = 0u;
        }
    }
    let _e510 = local_115;
    if (_e510 == 0u) {
    } else {
        return;
    }
    let _e512 = local_108;
    let _e513 = local_40;
    local_117 = (_e512 * _e513);
    let _e515 = local_62;
    let _e516 = local_75;
    local_118 = (_e515 + _e516);
    let _e518 = local_117;
    let _e519 = local_118;
    local_119 = (_e518 / _e519);
    let _e521 = local_119;
    local_120 = _e521;
    let _e522 = local_97;
    let _e523 = local_104;
    local_121 = (_e522 / _e523);
    let _e525 = local_121;
    local_122 = _e525;
    let _e526 = local_99;
    let _e527 = local_104;
    local_123 = (_e526 / _e527);
    let _e529 = local_123;
    local_124 = _e529;
    let _e530 = local_122;
    let _e531 = local_120;
    local_125 = (_e530 * _e531);
    let _e533 = local_125;
    let _e534 = local_62;
    local_126 = (_e533 * _e534);
    let _e536 = local_47;
    let _e537 = local_126;
    local_127 = (_e536 + _e537);
    let _e539 = local_17;
    local_128 = (_e539 * 2u);
    let _e541 = local_128;
    local_129 = _e541;
    let _e542 = local_129;
    local_130 = _e542;
    let _e543 = local_130;
    local_131 = (_e543 * 4u);
    let _e545 = local;
    let _e546 = local_131;
    local_132 = (_e545 + _e546);
    let _e548 = local_132;
    let _e553 = local_127;
    positions.member[(_e548 >> bitcast<u32>(2u))] = _e553;
    let _e554 = local_124;
    let _e555 = local_120;
    local_133 = (_e554 * _e555);
    let _e557 = local_133;
    let _e558 = local_62;
    local_134 = (_e557 * _e558);
    let _e560 = local_55;
    let _e561 = local_134;
    local_135 = (_e560 + _e561);
    let _e563 = local_17;
    local_136 = (_e563 * 2u);
    let _e565 = local_136;
    local_137 = (_e565 + 1u);
    let _e567 = local_137;
    local_138 = _e567;
    let _e568 = local_138;
    local_139 = _e568;
    let _e569 = local_139;
    local_140 = (_e569 * 4u);
    let _e571 = local;
    let _e572 = local_140;
    local_141 = (_e571 + _e572);
    let _e574 = local_141;
    let _e579 = local_135;
    positions.member[(_e574 >> bitcast<u32>(2u))] = _e579;
    let _e580 = local_23;
    local_142 = select(0u, 1u, (_e580 != 4294967295u));
    let _e583 = local_142;
    if (_e583 == 0u) {
    } else {
        let _e585 = local_122;
        let _e586 = local_120;
        local_143 = (_e585 * _e586);
        let _e588 = local_143;
        let _e589 = local_75;
        local_144 = (_e588 * _e589);
        let _e591 = local_68;
        let _e592 = local_144;
        local_145 = (_e591 - _e592);
        let _e594 = local_23;
        local_146 = (_e594 * 2u);
        let _e596 = local_146;
        local_147 = _e596;
        let _e597 = local_147;
        local_148 = _e597;
        let _e598 = local_148;
        local_149 = (_e598 * 4u);
        let _e600 = local;
        let _e601 = local_149;
        local_150 = (_e600 + _e601);
        let _e603 = local_150;
        let _e608 = local_145;
        positions.member[(_e603 >> bitcast<u32>(2u))] = _e608;
        let _e609 = local_124;
        let _e610 = local_120;
        local_151 = (_e609 * _e610);
        let _e612 = local_151;
        let _e613 = local_75;
        local_152 = (_e612 * _e613);
        let _e615 = local_74;
        let _e616 = local_152;
        local_153 = (_e615 - _e616);
        let _e618 = local_23;
        local_154 = (_e618 * 2u);
        let _e620 = local_154;
        local_155 = (_e620 + 1u);
        let _e622 = local_155;
        local_156 = _e622;
        let _e623 = local_156;
        local_157 = _e623;
        let _e624 = local_157;
        local_158 = (_e624 * 4u);
        let _e626 = local;
        let _e627 = local_158;
        local_159 = (_e626 + _e627);
        let _e629 = local_159;
        let _e634 = local_153;
        positions.member[(_e629 >> bitcast<u32>(2u))] = _e634;
    }
    return;
}

fn unsplit_by_bits(param: u32) -> u32 {
    var local_160: u32;
    var local_161: u32;
    var local_162: u32;
    var local_163: u32;
    var local_164: u32;
    var local_165: u32;
    var local_166: u32;
    var local_167: u32;
    var local_168: u32;
    var local_169: u32;
    var local_170: u32;
    var local_171: u32;
    var local_172: u32;
    var local_173: u32;
    var local_174: u32;

    local_160 = param;
    let _e84 = local_160;
    local_161 = (_e84 & 1431655765u);
    let _e86 = local_161;
    local_162 = _e86;
    let _e87 = local_162;
    local_163 = (_e87 >> bitcast<u32>((1u & 31u)));
    let _e91 = local_162;
    let _e92 = local_163;
    local_164 = (_e91 | _e92);
    let _e94 = local_164;
    local_165 = (_e94 & 858993459u);
    let _e96 = local_165;
    local_162 = _e96;
    let _e97 = local_162;
    local_166 = (_e97 >> bitcast<u32>((2u & 31u)));
    let _e101 = local_162;
    let _e102 = local_166;
    local_167 = (_e101 | _e102);
    let _e104 = local_167;
    local_168 = (_e104 & 252645135u);
    let _e106 = local_168;
    local_162 = _e106;
    let _e107 = local_162;
    local_169 = (_e107 >> bitcast<u32>((4u & 31u)));
    let _e111 = local_162;
    let _e112 = local_169;
    local_170 = (_e111 | _e112);
    let _e114 = local_170;
    local_171 = (_e114 & 16711935u);
    let _e116 = local_171;
    local_162 = _e116;
    let _e117 = local_162;
    local_172 = (_e117 >> bitcast<u32>((8u & 31u)));
    let _e121 = local_162;
    let _e122 = local_172;
    local_173 = (_e121 | _e122);
    let _e124 = local_173;
    local_174 = (_e124 & 65535u);
    let _e126 = local_174;
    local_162 = _e126;
    let _e127 = local_162;
    return _e127;
}

fn get_cell_color(param_1: u32) -> u32 {
    var local_175: u32;
    var local_176: u32;
    var local_177: u32;
    var local_178: u32;
    var local_179: u32;
    var local_180: u32;
    var local_181: u32;
    var local_182: u32;
    var local_183: u32;
    var local_184: u32;
    var local_185: u32;

    local_175 = param_1;
    let _e80 = local_175;
    let _e81 = unsplit_by_bits(_e80);
    local_176 = _e81;
    let _e82 = local_176;
    local_177 = _e82;
    let _e83 = local_175;
    local_178 = (_e83 >> bitcast<u32>((1u & 31u)));
    let _e87 = local_178;
    let _e88 = unsplit_by_bits(_e87);
    local_179 = _e88;
    let _e89 = local_179;
    local_180 = _e89;
    let _e90 = local_177;
    local_181 = (_e90 % 2u);
    let _e92 = local_181;
    local_182 = (1u + _e92);
    let _e94 = local_180;
    local_183 = (_e94 % 2u);
    let _e96 = local_183;
    local_184 = (_e96 * 2u);
    let _e98 = local_182;
    let _e99 = local_184;
    local_185 = (_e98 + _e99);
    let _e101 = local_185;
    return _e101;
}

fn solve_collisions_grouped_1() {
    var local_186: u32;
    var local_187: u32;
    var local_188: u32;
    var local_189: u32;
    var local_190: u32;
    var local_191: u32;
    var local_192: u32;
    var local_193: u32;
    var local_194: u32;
    var local_195: u32;
    var local_196: u32;
    var local_197: u32;
    var local_198: u32;
    var local_199: u32;
    var local_200: u32;
    var local_201: u32;
    var local_202: u32;
    var local_203: u32;
    var local_204: u32;
    var local_205: u32;
    var local_206: u32;
    var local_207: u32;
    var local_208: u32;
    var local_209: u32;
    var local_210: u32;
    var local_211: u32;
    var local_212: u32;
    var local_213: u32;
    var local_214: u32;
    var local_215: u32;
    var local_216: u32;
    var local_217: u32;
    var local_218: u32;
    var local_219: u32;
    var local_220: u32;
    var local_221: u32;
    var local_222: u32;
    var local_223: u32;
    var local_224: u32;
    var local_225: u32;
    var local_226: u32;
    var local_227: u32;
    var local_228: u32;
    var local_229: u32;
    var local_230: u32;
    var local_231: u32;
    var local_232: u32;
    var local_233: u32;
    var local_234: u32;
    var local_235: u32;
    var local_236: u32;
    var local_237: u32;
    var local_238: u32;
    var local_239: u32;
    var local_240: u32;
    var local_241: u32;
    var local_242: u32;
    var local_243: u32;
    var local_244: u32;
    var local_245: u32;
    var local_246: u32;
    var local_247: u32;
    var local_248: u32;
    var local_249: u32;
    var local_250: u32;
    var local_251: u32;
    var local_252: u32;
    var local_253: u32;
    var local_254: u32;
    var local_255: u32;
    var local_256: u32;
    var local_257: u32;
    var local_258: u32;
    var local_259: u32;
    var local_260: u32;
    var local_261: u32;
    var local_262: u32;
    var local_263: u32;
    var local_264: u32;
    var local_265: u32;
    var local_266: u32;
    var local_267: u32;
    var local_268: u32;
    var local_269: u32;
    var local_270: u32;
    var local_271: u32;
    var local_272: u32;
    var local_273: u32;
    var local_274: u32;
    var local_275: u32;
    var local_276: u32;
    var local_277: u32;
    var local_278: u32;
    var local_279: f32;
    var local_280: f32;
    var local_281: u32;
    var local_282: u32;
    var local_283: u32;
    var local_284: u32;
    var local_285: u32;
    var local_286: f32;
    var local_287: f32;
    var local_288: u32;
    var local_289: u32;
    var local_290: u32;
    var local_291: u32;
    var local_292: f32;
    var local_293: f32;
    var local_294: u32;
    var local_295: u32;
    var local_296: u32;
    var local_297: u32;
    var local_298: u32;
    var local_299: f32;
    var local_300: f32;
    var local_301: u32;
    var local_302: u32;
    var local_303: u32;
    var local_304: f32;
    var local_305: f32;
    var local_306: u32;
    var local_307: u32;
    var local_308: u32;
    var local_309: f32;
    var local_310: f32;
    var local_311: f32;
    var local_312: f32;
    var local_313: f32;
    var local_314: f32;
    var local_315: f32;
    var local_316: f32;
    var local_317: f32;
    var local_318: f32;
    var local_319: f32;
    var local_320: f32;
    var local_321: f32;
    var local_322: f32;
    var local_323: f32;
    var local_324: u32;
    var local_325: u32;
    var local_326: f32;
    var local_327: u32;
    var local_328: f32;
    var local_329: f32;
    var local_330: f32;
    var local_331: f32;
    var local_332: f32;
    var local_333: f32;
    var local_334: f32;
    var local_335: f32;
    var local_336: f32;
    var local_337: f32;
    var local_338: f32;
    var local_339: f32;
    var local_340: f32;
    var local_341: f32;
    var local_342: f32;
    var local_343: f32;
    var local_344: f32;
    var local_345: f32;
    var local_346: f32;
    var local_347: f32;
    var local_348: f32;
    var local_349: f32;
    var local_350: f32;
    var local_351: f32;
    var local_352: f32;
    var local_353: f32;
    var local_354: u32;
    var local_355: u32;
    var local_356: u32;
    var local_357: u32;
    var local_358: f32;
    var local_359: f32;
    var local_360: u32;
    var local_361: u32;
    var local_362: u32;
    var local_363: u32;
    var local_364: u32;
    var local_365: f32;
    var local_366: f32;
    var local_367: u32;
    var local_368: u32;
    var local_369: u32;
    var local_370: u32;
    var local_371: f32;
    var local_372: f32;
    var local_373: u32;
    var local_374: u32;
    var local_375: u32;
    var local_376: u32;
    var local_377: u32;
    var local_378: u32;
    var local_379: u32;

    local_186 = 0u;
    local_187 = 0u;
    local_188 = 0u;
    local_189 = 0u;
    local_190 = 0u;
    local_191 = 0u;
    local_192 = 0u;
    local_193 = 0u;
    let _e263 = solve_collisions_grouped_args.current_cell_color;
    local_194 = _e263;
    let _e265 = gl_GlobalInvocationId_6[0u];
    local_195 = _e265;
    let _e266 = local_195;
    local_196 = _e266;
    local_197 = (0u * 4u);
    let _e268 = local_192;
    let _e269 = local_197;
    local_198 = (_e268 + _e269);
    let _e271 = local_198;
    let _e276 = uniform_data.member[(_e271 >> bitcast<u32>(2u))];
    local_199 = _e276;
    let _e277 = local_199;
    local_200 = _e277;
    local_201 = (1u * 4u);
    let _e279 = local_192;
    let _e280 = local_201;
    local_202 = (_e279 + _e280);
    let _e282 = local_202;
    let _e287 = uniform_data.member[(_e282 >> bitcast<u32>(2u))];
    local_203 = _e287;
    let _e288 = local_203;
    local_204 = _e288;
    let _e289 = local_200;
    local_205 = (_e289 - 1u);
    let _e291 = local_205;
    local_206 = _e291;
    let _e292 = local_206;
    local_207 = _e292;
    let _e293 = local_207;
    local_208 = (_e293 * 4u);
    let _e295 = local_186;
    let _e296 = local_208;
    local_209 = (_e295 + _e296);
    let _e298 = local_209;
    let _e303 = chunk_obj_count.member[(_e298 >> bitcast<u32>(2u))];
    local_210 = _e303;
    let _e304 = local_210;
    local_211 = _e304;
    let _e305 = local_196;
    let _e306 = local_211;
    local_212 = select(0u, 1u, (_e305 >= _e306));
    let _e309 = local_212;
    if (_e309 == 0u) {
        let _e311 = local_196;
        local_213 = _e311;
        let _e312 = local_213;
        local_214 = _e312;
        let _e313 = local_214;
        local_215 = (_e313 * 4u);
        let _e315 = local_187;
        let _e316 = local_215;
        local_216 = (_e315 + _e316);
        let _e318 = local_216;
        let _e323 = collision_cells.member[(_e318 >> bitcast<u32>(2u))];
        local_217 = _e323;
        let _e324 = local_217;
        local_218 = _e324;
        let _e325 = local_218;
        local_219 = _e325;
        let _e326 = local_219;
        local_220 = _e326;
        let _e327 = local_220;
        local_221 = (_e327 * 4u);
        let _e329 = local_188;
        let _e330 = local_221;
        local_222 = (_e329 + _e330);
        let _e332 = local_222;
        let _e337 = cell_ids.member[(_e332 >> bitcast<u32>(2u))];
        local_223 = _e337;
        let _e338 = local_223;
        local_224 = _e338;
        let _e339 = local_224;
        let _e340 = get_cell_color(_e339);
        local_225 = _e340;
        let _e341 = local_225;
        let _e342 = local_194;
        local_226 = select(0u, 1u, (_e341 != _e342));
        let _e345 = local_226;
        if (_e345 == 0u) {
            let _e347 = local_218;
            local_227 = _e347;
            loop {
                let _e348 = local_227;
                let _e349 = local_204;
                local_228 = select(0u, 1u, (_e348 < _e349));
                let _e352 = local_228;
                if (_e352 == 0u) {
                    break;
                } else {
                    let _e354 = local_227;
                    local_229 = _e354;
                    let _e355 = local_229;
                    local_230 = _e355;
                    let _e356 = local_230;
                    local_231 = (_e356 * 4u);
                    let _e358 = local_188;
                    let _e359 = local_231;
                    local_232 = (_e358 + _e359);
                    let _e361 = local_232;
                    let _e366 = cell_ids.member[(_e361 >> bitcast<u32>(2u))];
                    local_233 = _e366;
                    let _e367 = local_233;
                    let _e368 = local_224;
                    local_234 = select(0u, 1u, (_e367 != _e368));
                    let _e371 = local_234;
                    if (_e371 == 0u) {
                        let _e373 = local_227;
                        local_235 = _e373;
                        let _e374 = local_235;
                        local_236 = _e374;
                        let _e375 = local_236;
                        local_237 = (_e375 * 4u);
                        let _e377 = local_189;
                        let _e378 = local_237;
                        local_238 = (_e377 + _e378);
                        let _e380 = local_238;
                        let _e385 = object_ids.member[(_e380 >> bitcast<u32>(2u))];
                        local_239 = _e385;
                        let _e386 = local_239;
                        local_240 = _e386;
                        let _e387 = local_240;
                        local_241 = _e387;
                        let _e388 = local_227;
                        local_242 = (_e388 + 1u);
                        let _e390 = local_242;
                        local_243 = _e390;
                        loop {
                            let _e391 = local_243;
                            let _e392 = local_204;
                            local_244 = select(0u, 1u, (_e391 < _e392));
                            let _e395 = local_244;
                            if (_e395 == 0u) {
                                let _e397 = local_227;
                                local_379 = (_e397 + 1u);
                                let _e399 = local_379;
                                local_227 = _e399;
                                break;
                            }
                            let _e400 = local_243;
                            local_245 = _e400;
                            let _e401 = local_245;
                            local_246 = _e401;
                            let _e402 = local_246;
                            local_247 = (_e402 * 4u);
                            let _e404 = local_188;
                            let _e405 = local_247;
                            local_248 = (_e404 + _e405);
                            let _e407 = local_248;
                            let _e412 = cell_ids.member[(_e407 >> bitcast<u32>(2u))];
                            local_249 = _e412;
                            let _e413 = local_249;
                            let _e414 = local_224;
                            local_250 = select(0u, 1u, (_e413 != _e414));
                            let _e417 = local_250;
                            if (_e417 == 0u) {
                            } else {
                                let _e419 = local_227;
                                local_379 = (_e419 + 1u);
                                let _e421 = local_379;
                                local_227 = _e421;
                                break;
                            }
                            let _e422 = local_243;
                            local_251 = _e422;
                            let _e423 = local_251;
                            local_252 = _e423;
                            let _e424 = local_252;
                            local_253 = (_e424 * 4u);
                            let _e426 = local_189;
                            let _e427 = local_253;
                            local_254 = (_e426 + _e427);
                            let _e429 = local_254;
                            let _e434 = object_ids.member[(_e429 >> bitcast<u32>(2u))];
                            local_255 = _e434;
                            let _e435 = local_255;
                            local_256 = _e435;
                            let _e436 = local_256;
                            local_257 = _e436;
                            let _e437 = local_241;
                            local_258 = _e437;
                            let _e438 = local_258;
                            local_259 = (_e438 * 4u);
                            let _e440 = local_193;
                            let _e441 = local_259;
                            local_260 = (_e440 + _e441);
                            let _e443 = local_260;
                            let _e448 = groups.member[(_e443 >> bitcast<u32>(2u))];
                            local_261 = _e448;
                            let _e449 = local_261;
                            local_262 = select(0u, 1u, (_e449 != 0u));
                            local_263 = 1u;
                            let _e452 = local_262;
                            if (_e452 == 0u) {
                                local_263 = 0u;
                            } else {
                                let _e454 = local_241;
                                local_264 = _e454;
                                let _e455 = local_264;
                                local_265 = (_e455 * 4u);
                                let _e457 = local_193;
                                let _e458 = local_265;
                                local_266 = (_e457 + _e458);
                                let _e460 = local_266;
                                let _e465 = groups.member[(_e460 >> bitcast<u32>(2u))];
                                local_267 = _e465;
                                let _e466 = local_257;
                                local_268 = _e466;
                                let _e467 = local_268;
                                local_269 = (_e467 * 4u);
                                let _e469 = local_193;
                                let _e470 = local_269;
                                local_270 = (_e469 + _e470);
                                let _e472 = local_270;
                                let _e477 = groups.member[(_e472 >> bitcast<u32>(2u))];
                                local_271 = _e477;
                                let _e478 = local_267;
                                let _e479 = local_271;
                                local_272 = select(0u, 1u, (_e478 == _e479));
                                let _e482 = local_272;
                                if (_e482 == 0u) {
                                    local_263 = 0u;
                                }
                            }
                            let _e484 = local_263;
                            local_273 = select(0u, 1u, (_e484 != 0u));
                            local_274 = 1u;
                            let _e487 = local_273;
                            if (_e487 == 0u) {
                            } else {
                                local_274 = 0u;
                            }
                            let _e489 = local_274;
                            if (_e489 == 0u) {
                            } else {
                                let _e491 = local_241;
                                local_275 = (_e491 * 2u);
                                let _e493 = local_275;
                                local_276 = _e493;
                                let _e494 = local_276;
                                local_277 = (_e494 * 4u);
                                let _e496 = local_190;
                                let _e497 = local_277;
                                local_278 = (_e496 + _e497);
                                let _e499 = local_278;
                                let _e504 = positions_1.member[(_e499 >> bitcast<u32>(2u))];
                                local_279 = _e504;
                                let _e505 = local_279;
                                local_280 = _e505;
                                let _e506 = local_241;
                                local_281 = (_e506 * 2u);
                                let _e508 = local_281;
                                local_282 = (_e508 + 1u);
                                let _e510 = local_282;
                                local_283 = _e510;
                                let _e511 = local_283;
                                local_284 = (_e511 * 4u);
                                let _e513 = local_190;
                                let _e514 = local_284;
                                local_285 = (_e513 + _e514);
                                let _e516 = local_285;
                                let _e521 = positions_1.member[(_e516 >> bitcast<u32>(2u))];
                                local_286 = _e521;
                                let _e522 = local_286;
                                local_287 = _e522;
                                let _e523 = local_257;
                                local_288 = (_e523 * 2u);
                                let _e525 = local_288;
                                local_289 = _e525;
                                let _e526 = local_289;
                                local_290 = (_e526 * 4u);
                                let _e528 = local_190;
                                let _e529 = local_290;
                                local_291 = (_e528 + _e529);
                                let _e531 = local_291;
                                let _e536 = positions_1.member[(_e531 >> bitcast<u32>(2u))];
                                local_292 = _e536;
                                let _e537 = local_292;
                                local_293 = _e537;
                                let _e538 = local_257;
                                local_294 = (_e538 * 2u);
                                let _e540 = local_294;
                                local_295 = (_e540 + 1u);
                                let _e542 = local_295;
                                local_296 = _e542;
                                let _e543 = local_296;
                                local_297 = (_e543 * 4u);
                                let _e545 = local_190;
                                let _e546 = local_297;
                                local_298 = (_e545 + _e546);
                                let _e548 = local_298;
                                let _e553 = positions_1.member[(_e548 >> bitcast<u32>(2u))];
                                local_299 = _e553;
                                let _e554 = local_299;
                                local_300 = _e554;
                                let _e555 = local_241;
                                local_301 = _e555;
                                let _e556 = local_301;
                                local_302 = (_e556 * 4u);
                                let _e558 = local_191;
                                let _e559 = local_302;
                                local_303 = (_e558 + _e559);
                                let _e561 = local_303;
                                let _e566 = radius_1.member[(_e561 >> bitcast<u32>(2u))];
                                local_304 = _e566;
                                let _e567 = local_304;
                                local_305 = _e567;
                                let _e568 = local_257;
                                local_306 = _e568;
                                let _e569 = local_306;
                                local_307 = (_e569 * 4u);
                                let _e571 = local_191;
                                let _e572 = local_307;
                                local_308 = (_e571 + _e572);
                                let _e574 = local_308;
                                let _e579 = radius_1.member[(_e574 >> bitcast<u32>(2u))];
                                local_309 = _e579;
                                let _e580 = local_309;
                                local_310 = _e580;
                                let _e581 = local_280;
                                let _e582 = local_293;
                                local_311 = (_e581 - _e582);
                                let _e584 = local_311;
                                local_312 = _e584;
                                let _e585 = local_287;
                                let _e586 = local_300;
                                local_313 = (_e585 - _e586);
                                let _e588 = local_313;
                                local_314 = _e588;
                                let _e589 = local_312;
                                let _e590 = local_312;
                                local_315 = (_e589 * _e590);
                                let _e592 = local_314;
                                let _e593 = local_314;
                                local_316 = (_e592 * _e593);
                                let _e595 = local_315;
                                let _e596 = local_316;
                                local_317 = (_e595 + _e596);
                                let _e598 = local_317;
                                local_318 = sqrt(_e598);
                                let _e600 = local_318;
                                local_319 = _e600;
                                let _e601 = local_305;
                                let _e602 = local_310;
                                local_320 = (_e601 + _e602);
                                let _e604 = local_320;
                                local_321 = _e604;
                                let _e605 = local_321;
                                let _e606 = local_321;
                                local_322 = (_e605 * _e606);
                                let _e608 = local_319;
                                let _e609 = local_319;
                                local_323 = (_e608 * _e609);
                                let _e611 = local_322;
                                let _e612 = local_323;
                                local_324 = select(0u, 1u, (_e611 > _e612));
                                local_325 = 1u;
                                let _e615 = local_324;
                                if (_e615 == 0u) {
                                    local_325 = 0u;
                                } else {
                                    local_326 = 0.0001f;
                                    let _e617 = local_319;
                                    let _e618 = local_326;
                                    local_327 = select(0u, 1u, (_e617 > _e618));
                                    let _e621 = local_327;
                                    if (_e621 == 0u) {
                                        local_325 = 0u;
                                    }
                                }
                                let _e623 = local_325;
                                if (_e623 == 0u) {
                                } else {
                                    let _e625 = local_321;
                                    let _e626 = local_319;
                                    local_328 = (_e625 - _e626);
                                    let _e628 = local_328;
                                    local_329 = _e628;
                                    let _e629 = local_312;
                                    let _e630 = local_319;
                                    local_330 = (_e629 / _e630);
                                    let _e632 = local_330;
                                    local_331 = _e632;
                                    let _e633 = local_314;
                                    let _e634 = local_319;
                                    local_332 = (_e633 / _e634);
                                    let _e636 = local_332;
                                    local_333 = _e636;
                                    let _e637 = local_331;
                                    let _e638 = local_329;
                                    local_334 = (_e637 * _e638);
                                    local_335 = 0.6f;
                                    let _e640 = local_334;
                                    let _e641 = local_335;
                                    local_336 = (_e640 * _e641);
                                    let _e643 = local_336;
                                    local_337 = _e643;
                                    let _e644 = local_333;
                                    let _e645 = local_329;
                                    local_338 = (_e644 * _e645);
                                    local_339 = 0.6f;
                                    let _e647 = local_338;
                                    let _e648 = local_339;
                                    local_340 = (_e647 * _e648);
                                    let _e650 = local_340;
                                    local_341 = _e650;
                                    let _e651 = local_305;
                                    local_342 = (1f / _e651);
                                    let _e653 = local_342;
                                    local_343 = _e653;
                                    let _e654 = local_310;
                                    local_344 = (1f / _e654);
                                    let _e656 = local_344;
                                    local_345 = _e656;
                                    let _e657 = local_343;
                                    let _e658 = local_345;
                                    local_346 = (_e657 + _e658);
                                    let _e660 = local_343;
                                    let _e661 = local_346;
                                    local_347 = (_e660 / _e661);
                                    let _e663 = local_347;
                                    local_348 = _e663;
                                    let _e664 = local_343;
                                    let _e665 = local_345;
                                    local_349 = (_e664 + _e665);
                                    let _e667 = local_345;
                                    let _e668 = local_349;
                                    local_350 = (_e667 / _e668);
                                    let _e670 = local_350;
                                    local_351 = _e670;
                                    let _e671 = local_337;
                                    let _e672 = local_348;
                                    local_352 = (_e671 * _e672);
                                    let _e674 = local_280;
                                    let _e675 = local_352;
                                    local_353 = (_e674 + _e675);
                                    let _e677 = local_241;
                                    local_354 = (_e677 * 2u);
                                    let _e679 = local_354;
                                    local_355 = _e679;
                                    let _e680 = local_355;
                                    local_356 = (_e680 * 4u);
                                    let _e682 = local_190;
                                    let _e683 = local_356;
                                    local_357 = (_e682 + _e683);
                                    let _e685 = local_357;
                                    let _e690 = local_353;
                                    positions_1.member[(_e685 >> bitcast<u32>(2u))] = _e690;
                                    let _e691 = local_341;
                                    let _e692 = local_348;
                                    local_358 = (_e691 * _e692);
                                    let _e694 = local_287;
                                    let _e695 = local_358;
                                    local_359 = (_e694 + _e695);
                                    let _e697 = local_241;
                                    local_360 = (_e697 * 2u);
                                    let _e699 = local_360;
                                    local_361 = (_e699 + 1u);
                                    let _e701 = local_361;
                                    local_362 = _e701;
                                    let _e702 = local_362;
                                    local_363 = (_e702 * 4u);
                                    let _e704 = local_190;
                                    let _e705 = local_363;
                                    local_364 = (_e704 + _e705);
                                    let _e707 = local_364;
                                    let _e712 = local_359;
                                    positions_1.member[(_e707 >> bitcast<u32>(2u))] = _e712;
                                    let _e713 = local_337;
                                    let _e714 = local_351;
                                    local_365 = (_e713 * _e714);
                                    let _e716 = local_293;
                                    let _e717 = local_365;
                                    local_366 = (_e716 - _e717);
                                    let _e719 = local_257;
                                    local_367 = (_e719 * 2u);
                                    let _e721 = local_367;
                                    local_368 = _e721;
                                    let _e722 = local_368;
                                    local_369 = (_e722 * 4u);
                                    let _e724 = local_190;
                                    let _e725 = local_369;
                                    local_370 = (_e724 + _e725);
                                    let _e727 = local_370;
                                    let _e732 = local_366;
                                    positions_1.member[(_e727 >> bitcast<u32>(2u))] = _e732;
                                    let _e733 = local_341;
                                    let _e734 = local_351;
                                    local_371 = (_e733 * _e734);
                                    let _e736 = local_300;
                                    let _e737 = local_371;
                                    local_372 = (_e736 - _e737);
                                    let _e739 = local_257;
                                    local_373 = (_e739 * 2u);
                                    let _e741 = local_373;
                                    local_374 = (_e741 + 1u);
                                    let _e743 = local_374;
                                    local_375 = _e743;
                                    let _e744 = local_375;
                                    local_376 = (_e744 * 4u);
                                    let _e746 = local_190;
                                    let _e747 = local_376;
                                    local_377 = (_e746 + _e747);
                                    let _e749 = local_377;
                                    let _e754 = local_372;
                                    positions_1.member[(_e749 >> bitcast<u32>(2u))] = _e754;
                                }
                            }
                            let _e755 = local_243;
                            local_378 = (_e755 + 1u);
                            let _e757 = local_378;
                            local_243 = _e757;
                            continue;
                        }
                        continue;
                    } else {
                        break;
                    }
                }
            }
            return;
        } else {
            return;
        }
    } else {
        return;
    }
}

fn integrate_tagged_1() {
    var local_380: u32;
    var local_381: u32;
    var local_382: u32;
    var local_383: u32;
    var local_384: f32;
    var local_385: f32;
    var local_386: f32;
    var local_387: f32;
    var local_388: f32;
    var local_389: f32;
    var local_390: f32;
    var local_391: u32;
    var local_392: u32;
    var local_393: u32;
    var local_394: u32;
    var local_395: u32;
    var local_396: u32;
    var local_397: u32;
    var local_398: u32;
    var local_399: u32;
    var local_400: u32;
    var local_401: f32;
    var local_402: f32;
    var local_403: u32;
    var local_404: u32;
    var local_405: u32;
    var local_406: u32;
    var local_407: f32;
    var local_408: f32;
    var local_409: f32;
    var local_410: u32;
    var local_411: u32;
    var local_412: u32;
    var local_413: u32;
    var local_414: u32;
    var local_415: u32;
    var local_416: u32;
    var local_417: u32;
    var local_418: u32;
    var local_419: f32;
    var local_420: f32;
    var local_421: f32;
    var local_422: f32;
    var local_423: u32;
    var local_424: u32;
    var local_425: u32;
    var local_426: u32;
    var local_427: f32;
    var local_428: f32;
    var local_429: f32;
    var local_430: f32;
    var local_431: f32;
    var local_432: f32;
    var local_433: f32;
    var local_434: f32;
    var local_435: f32;
    var local_436: f32;
    var local_437: f32;
    var local_438: f32;
    var local_439: f32;
    var local_440: f32;
    var local_441: u32;
    var local_442: u32;
    var local_443: u32;
    var local_444: u32;
    var local_445: u32;
    var local_446: u32;
    var local_447: u32;
    var local_448: u32;
    var local_449: u32;
    var local_450: u32;
    var local_451: u32;
    var local_452: f32;
    var local_453: f32;
    var local_454: f32;
    var local_455: f32;
    var local_456: f32;
    var local_457: f32;
    var local_458: f32;
    var local_459: f32;
    var local_460: u32;
    var local_461: u32;
    var local_462: u32;
    var local_463: u32;
    var local_464: u32;
    var local_465: u32;
    var local_466: u32;

    local_380 = 0u;
    local_381 = 0u;
    local_382 = 0u;
    local_383 = 0u;
    let _e156 = integrate_tagged_args.delta_time;
    local_384 = _e156;
    let _e158 = integrate_tagged_args.gravity_x;
    local_385 = _e158;
    let _e160 = integrate_tagged_args.gravity_y;
    local_386 = _e160;
    let _e162 = integrate_tagged_args.damping;
    local_387 = _e162;
    let _e164 = integrate_tagged_args.sand_damping;
    local_388 = _e164;
    let _e166 = integrate_tagged_args.world_width;
    local_389 = _e166;
    let _e168 = integrate_tagged_args.world_height;
    local_390 = _e168;
    let _e170 = integrate_tagged_args.num_particles;
    local_391 = _e170;
    let _e172 = gl_GlobalInvocationId_6[0u];
    local_392 = _e172;
    let _e173 = local_392;
    local_393 = _e173;
    let _e174 = local_393;
    let _e175 = local_391;
    local_394 = select(0u, 1u, (_e174 >= _e175));
    let _e178 = local_394;
    if (_e178 == 0u) {
    } else {
        return;
    }
    let _e180 = local_393;
    local_395 = (_e180 * 2u);
    let _e182 = local_395;
    local_396 = _e182;
    let _e183 = local_396;
    local_397 = _e183;
    let _e184 = local_397;
    local_398 = _e184;
    let _e185 = local_398;
    local_399 = (_e185 * 4u);
    let _e187 = local_380;
    let _e188 = local_399;
    local_400 = (_e187 + _e188);
    let _e190 = local_400;
    let _e195 = positions_2.member[(_e190 >> bitcast<u32>(2u))];
    local_401 = _e195;
    let _e196 = local_401;
    local_402 = _e196;
    let _e197 = local_397;
    local_403 = (_e197 + 1u);
    let _e199 = local_403;
    local_404 = _e199;
    let _e200 = local_404;
    local_405 = (_e200 * 4u);
    let _e202 = local_380;
    let _e203 = local_405;
    local_406 = (_e202 + _e203);
    let _e205 = local_406;
    let _e210 = positions_2.member[(_e205 >> bitcast<u32>(2u))];
    local_407 = _e210;
    let _e211 = local_407;
    local_408 = _e211;
    let _e212 = local_387;
    local_409 = _e212;
    let _e213 = local_393;
    local_410 = _e213;
    let _e214 = local_410;
    local_411 = _e214;
    let _e215 = local_411;
    local_412 = (_e215 * 4u);
    let _e217 = local_383;
    let _e218 = local_412;
    local_413 = (_e217 + _e218);
    let _e220 = local_413;
    let _e225 = tags.member[(_e220 >> bitcast<u32>(2u))];
    local_414 = _e225;
    let _e226 = local_414;
    local_415 = select(0u, 1u, (_e226 == 1u));
    let _e229 = local_415;
    if (_e229 == 0u) {
    } else {
        let _e231 = local_388;
        local_409 = _e231;
    }
    let _e232 = local_397;
    local_416 = _e232;
    let _e233 = local_416;
    local_417 = (_e233 * 4u);
    let _e235 = local_381;
    let _e236 = local_417;
    local_418 = (_e235 + _e236);
    let _e238 = local_418;
    let _e243 = previous_positions.member[(_e238 >> bitcast<u32>(2u))];
    local_419 = _e243;
    let _e244 = local_402;
    let _e245 = local_419;
    local_420 = (_e244 - _e245);
    let _e247 = local_420;
    let _e248 = local_409;
    local_421 = (_e247 * _e248);
    let _e250 = local_421;
    local_422 = _e250;
    let _e251 = local_397;
    local_423 = (_e251 + 1u);
    let _e253 = local_423;
    local_424 = _e253;
    let _e254 = local_424;
    local_425 = (_e254 * 4u);
    let _e256 = local_381;
    let _e257 = local_425;
    local_426 = (_e256 + _e257);
    let _e259 = local_426;
    let _e264 = previous_positions.member[(_e259 >> bitcast<u32>(2u))];
    local_427 = _e264;
    let _e265 = local_408;
    let _e266 = local_427;
    local_428 = (_e265 - _e266);
    let _e268 = local_428;
    let _e269 = local_409;
    local_429 = (_e268 * _e269);
    let _e271 = local_429;
    local_430 = _e271;
    let _e272 = local_384;
    let _e273 = local_384;
    local_431 = (_e272 * _e273);
    let _e275 = local_431;
    local_432 = _e275;
    let _e276 = local_402;
    let _e277 = local_422;
    local_433 = (_e276 + _e277);
    let _e279 = local_385;
    let _e280 = local_432;
    local_434 = (_e279 * _e280);
    let _e282 = local_433;
    let _e283 = local_434;
    local_435 = (_e282 + _e283);
    let _e285 = local_435;
    local_436 = _e285;
    let _e286 = local_408;
    let _e287 = local_430;
    local_437 = (_e286 + _e287);
    let _e289 = local_386;
    let _e290 = local_432;
    local_438 = (_e289 * _e290);
    let _e292 = local_437;
    let _e293 = local_438;
    local_439 = (_e292 + _e293);
    let _e295 = local_439;
    local_440 = _e295;
    let _e296 = local_397;
    local_441 = _e296;
    let _e297 = local_441;
    local_442 = (_e297 * 4u);
    let _e299 = local_381;
    let _e300 = local_442;
    local_443 = (_e299 + _e300);
    let _e302 = local_443;
    let _e307 = local_402;
    previous_positions.member[(_e302 >> bitcast<u32>(2u))] = _e307;
    let _e308 = local_397;
    local_444 = (_e308 + 1u);
    let _e310 = local_444;
    local_445 = _e310;
    let _e311 = local_445;
    local_446 = (_e311 * 4u);
    let _e313 = local_381;
    let _e314 = local_446;
    local_447 = (_e313 + _e314);
    let _e316 = local_447;
    let _e321 = local_408;
    previous_positions.member[(_e316 >> bitcast<u32>(2u))] = _e321;
    let _e322 = local_393;
    local_448 = _e322;
    let _e323 = local_448;
    local_449 = _e323;
    let _e324 = local_449;
    local_450 = (_e324 * 4u);
    let _e326 = local_382;
    let _e327 = local_450;
    local_451 = (_e326 + _e327);
    let _e329 = local_451;
    let _e334 = radius_2.member[(_e329 >> bitcast<u32>(2u))];
    local_452 = _e334;
    let _e335 = local_452;
    local_453 = _e335;
    let _e336 = local_436;
    let _e337 = local_453;
    local_454 = max(_e336, _e337);
    let _e339 = local_389;
    let _e340 = local_453;
    local_455 = (_e339 - _e340);
    let _e342 = local_454;
    let _e343 = local_455;
    local_456 = min(_e342, _e343);
    let _e345 = local_456;
    local_436 = _e345;
    let _e346 = local_440;
    let _e347 = local_453;
    local_457 = max(_e346, _e347);
    let _e349 = local_390;
    let _e350 = local_453;
    local_458 = (_e349 - _e350);
    let _e352 = local_457;
    let _e353 = local_458;
    local_459 = min(_e352, _e353);
    let _e355 = local_459;
    local_440 = _e355;
    let _e356 = local_397;
    local_460 = _e356;
    let _e357 = local_460;
    local_461 = (_e357 * 4u);
    let _e359 = local_380;
    let _e360 = local_461;
    local_462 = (_e359 + _e360);
    let _e362 = local_462;
    let _e367 = local_436;
    positions_2.member[(_e362 >> bitcast<u32>(2u))] = _e367;
    let _e368 = local_397;
    local_463 = (_e368 + 1u);
    let _e370 = local_463;
    local_464 = _e370;
    let _e371 = local_464;
    local_465 = (_e371 * 4u);
    let _e373 = local_380;
    let _e374 = local_465;
    local_466 = (_e373 + _e374);
    let _e376 = local_466;
    let _e381 = local_440;
    positions_2.member[(_e376 >> bitcast<u32>(2u))] = _e381;
    return;
}

fn tile_index(param_2: u32, param_3: u32, param_4: u32, param_5: u32) -> u32 {
    var local_467: u32;
    var local_468: u32;
    var local_469: u32;
    var local_470: u32;
    var local_471: u32;
    var local_472: u32;
    var local_473: u32;
    var local_474: u32;
    var local_475: u32;
    var local_476: u32;
    var local_477: u32;
    var local_478: u32;
    var local_479: u32;

    local_467 = param_2;
    local_468 = param_3;
    local_469 = param_4;
    local_470 = param_5;
    let _e85 = local_469;
    local_471 = select(0u, 1u, (bitcast<i32>(_e85) < bitcast<i32>(0u)));
    local_472 = 0u;
    let _e90 = local_471;
    if (_e90 != 0u) {
        local_472 = 1u;
    } else {
        let _e92 = local_470;
        local_473 = select(0u, 1u, (bitcast<i32>(_e92) < bitcast<i32>(0u)));
        let _e97 = local_473;
        if (_e97 != 0u) {
            local_472 = 1u;
        }
    }
    local_474 = 0u;
    let _e99 = local_472;
    if (_e99 != 0u) {
        local_474 = 1u;
    } else {
        let _e101 = local_469;
        let _e102 = local_467;
        local_475 = select(0u, 1u, (bitcast<i32>(_e101) >= bitcast<i32>(_e102)));
        let _e107 = local_475;
        if (_e107 != 0u) {
            local_474 = 1u;
        }
    }
    local_476 = 0u;
    let _e109 = local_474;
    if (_e109 != 0u) {
        local_476 = 1u;
    } else {
        let _e111 = local_470;
        let _e112 = local_468;
        local_477 = select(0u, 1u, (bitcast<i32>(_e111) >= bitcast<i32>(_e112)));
        let _e117 = local_477;
        if (_e117 != 0u) {
            local_476 = 1u;
        }
    }
    let _e119 = local_476;
    if (_e119 == 0u) {
        let _e121 = local_470;
        let _e122 = local_467;
        local_478 = (_e121 * _e122);
        let _e124 = local_478;
        let _e125 = local_469;
        local_479 = (_e124 + _e125);
        let _e127 = local_479;
        return _e127;
    } else {
        return 4294967295u;
    }
}

fn tile_friction_1() {
    var local_480: u32;
    var local_481: u32;
    var local_482: u32;
    var local_483: u32;
    var local_484: u32;
    var local_485: u32;
    var local_486: u32;
    var local_487: f32;
    var local_488: f32;
    var local_489: u32;
    var local_490: u32;
    var local_491: u32;
    var local_492: u32;
    var local_493: u32;
    var local_494: u32;
    var local_495: u32;
    var local_496: u32;
    var local_497: u32;
    var local_498: u32;
    var local_499: u32;
    var local_500: u32;
    var local_501: u32;
    var local_502: u32;
    var local_503: f32;
    var local_504: f32;
    var local_505: f32;
    var local_506: u32;
    var local_507: u32;
    var local_508: u32;
    var local_509: f32;
    var local_510: f32;
    var local_511: u32;
    var local_512: u32;
    var local_513: u32;
    var local_514: u32;
    var local_515: f32;
    var local_516: f32;
    var local_517: u32;
    var local_518: u32;
    var local_519: u32;
    var local_520: f32;
    var local_521: f32;
    var local_522: u32;
    var local_523: u32;
    var local_524: u32;
    var local_525: u32;
    var local_526: f32;
    var local_527: f32;
    var local_528: f32;
    var local_529: f32;
    var local_530: f32;
    var local_531: f32;
    var local_532: f32;
    var local_533: f32;
    var local_534: u32;
    var local_535: f32;
    var local_536: f32;
    var local_537: u32;
    var local_538: u32;
    var local_539: f32;
    var local_540: f32;
    var local_541: u32;
    var local_542: u32;
    var local_543: f32;
    var local_544: f32;
    var local_545: u32;
    var local_546: u32;
    var local_547: f32;
    var local_548: f32;
    var local_549: u32;
    var local_550: u32;
    var local_551: u32;
    var local_552: u32;
    var local_553: u32;
    var local_554: u32;
    var local_555: u32;
    var local_556: u32;
    var local_557: u32;
    var local_558: u32;
    var local_559: u32;
    var local_560: u32;
    var local_561: u32;
    var local_562: u32;
    var local_563: u32;
    var local_564: u32;
    var local_565: u32;
    var local_566: u32;
    var local_567: f32;
    var local_568: f32;
    var local_569: f32;
    var local_570: f32;
    var local_571: f32;
    var local_572: f32;
    var local_573: f32;
    var local_574: f32;
    var local_575: f32;
    var local_576: f32;
    var local_577: f32;
    var local_578: f32;
    var local_579: f32;
    var local_580: f32;
    var local_581: f32;
    var local_582: f32;
    var local_583: f32;
    var local_584: f32;
    var local_585: f32;
    var local_586: f32;
    var local_587: u32;
    var local_588: u32;
    var local_589: f32;
    var local_590: u32;
    var local_591: u32;
    var local_592: u32;
    var local_593: f32;
    var local_594: f32;
    var local_595: f32;
    var local_596: f32;
    var local_597: f32;
    var local_598: f32;
    var local_599: f32;
    var local_600: f32;
    var local_601: f32;
    var local_602: f32;
    var local_603: f32;
    var local_604: f32;
    var local_605: f32;
    var local_606: f32;
    var local_607: f32;
    var local_608: f32;
    var local_609: f32;
    var local_610: f32;
    var local_611: u32;
    var local_612: f32;
    var local_613: f32;
    var local_614: f32;
    var local_615: f32;
    var local_616: f32;
    var local_617: f32;
    var local_618: u32;
    var local_619: u32;
    var local_620: u32;
    var local_621: u32;
    var local_622: f32;
    var local_623: u32;
    var local_624: u32;
    var local_625: u32;
    var local_626: f32;
    var local_627: u32;
    var local_628: u32;
    var local_629: u32;
    var local_630: u32;

    local_480 = 0u;
    local_481 = 0u;
    local_482 = 0u;
    local_483 = 0u;
    let _e220 = tile_friction_args.tiles_w;
    local_484 = _e220;
    let _e222 = tile_friction_args.tiles_h;
    local_485 = _e222;
    let _e224 = tile_friction_args.num_particles;
    local_486 = _e224;
    let _e226 = tile_friction_args.mu;
    local_487 = _e226;
    let _e228 = tile_friction_args.absorb;
    local_488 = _e228;
    let _e230 = gl_GlobalInvocationId_6[0u];
    local_489 = _e230;
    let _e231 = local_489;
    local_490 = _e231;
    let _e232 = local_490;
    let _e233 = local_486;
    local_491 = select(0u, 1u, (_e232 >= _e233));
    let _e236 = local_491;
    if (_e236 == 0u) {
        let _e238 = local_490;
        local_492 = (_e238 * 2u);
        let _e240 = local_492;
        local_493 = _e240;
        let _e241 = local_493;
        local_494 = _e241;
        let _e242 = local_484;
        local_495 = _e242;
        let _e243 = local_495;
        local_496 = _e243;
        let _e244 = local_485;
        local_497 = _e244;
        let _e245 = local_497;
        local_498 = _e245;
        let _e246 = local_490;
        local_499 = _e246;
        let _e247 = local_499;
        local_500 = _e247;
        let _e248 = local_500;
        local_501 = (_e248 * 4u);
        let _e250 = local_482;
        let _e251 = local_501;
        local_502 = (_e250 + _e251);
        let _e253 = local_502;
        let _e258 = radius_3.member[(_e253 >> bitcast<u32>(2u))];
        local_503 = _e258;
        let _e259 = local_503;
        local_504 = (_e259 + 0.02f);
        let _e261 = local_504;
        local_505 = _e261;
        let _e262 = local_494;
        local_506 = _e262;
        let _e263 = local_506;
        local_507 = (_e263 * 4u);
        let _e265 = local_480;
        let _e266 = local_507;
        local_508 = (_e265 + _e266);
        let _e268 = local_508;
        let _e273 = positions_3.member[(_e268 >> bitcast<u32>(2u))];
        local_509 = _e273;
        let _e274 = local_509;
        local_510 = _e274;
        let _e275 = local_494;
        local_511 = (_e275 + 1u);
        let _e277 = local_511;
        local_512 = _e277;
        let _e278 = local_512;
        local_513 = (_e278 * 4u);
        let _e280 = local_480;
        let _e281 = local_513;
        local_514 = (_e280 + _e281);
        let _e283 = local_514;
        let _e288 = positions_3.member[(_e283 >> bitcast<u32>(2u))];
        local_515 = _e288;
        let _e289 = local_515;
        local_516 = _e289;
        let _e290 = local_494;
        local_517 = _e290;
        let _e291 = local_517;
        local_518 = (_e291 * 4u);
        let _e293 = local_481;
        let _e294 = local_518;
        local_519 = (_e293 + _e294);
        let _e296 = local_519;
        let _e301 = previous_positions_1.member[(_e296 >> bitcast<u32>(2u))];
        local_520 = _e301;
        let _e302 = local_520;
        local_521 = _e302;
        let _e303 = local_494;
        local_522 = (_e303 + 1u);
        let _e305 = local_522;
        local_523 = _e305;
        let _e306 = local_523;
        local_524 = (_e306 * 4u);
        let _e308 = local_481;
        let _e309 = local_524;
        local_525 = (_e308 + _e309);
        let _e311 = local_525;
        let _e316 = previous_positions_1.member[(_e311 >> bitcast<u32>(2u))];
        local_526 = _e316;
        let _e317 = local_526;
        local_527 = _e317;
        let _e318 = local_510;
        let _e319 = local_521;
        local_528 = (_e318 - _e319);
        let _e321 = local_528;
        local_529 = _e321;
        let _e322 = local_516;
        let _e323 = local_527;
        local_530 = (_e322 - _e323);
        let _e325 = local_530;
        local_531 = _e325;
        local_532 = 0f;
        local_533 = 0f;
        local_534 = select(0u, 1u, (0u != 0u));
        let _e328 = local_510;
        let _e329 = local_505;
        local_535 = (_e328 - _e329);
        let _e331 = local_535;
        local_536 = floor(_e331);
        let _e333 = local_536;
        let _e335 = select(_e333, 0f, (_e333 != _e333));
        local_537 = select(u32(clamp(_e335, -2147483600f, 2147483500f)), 2147483647u, (_e335 >= 2147483600f));
        let _e340 = local_537;
        local_538 = _e340;
        let _e341 = local_510;
        let _e342 = local_505;
        local_539 = (_e341 + _e342);
        let _e344 = local_539;
        local_540 = floor(_e344);
        let _e346 = local_540;
        let _e348 = select(_e346, 0f, (_e346 != _e346));
        local_541 = select(u32(clamp(_e348, -2147483600f, 2147483500f)), 2147483647u, (_e348 >= 2147483600f));
        let _e353 = local_541;
        local_542 = _e353;
        let _e354 = local_516;
        let _e355 = local_505;
        local_543 = (_e354 - _e355);
        let _e357 = local_543;
        local_544 = floor(_e357);
        let _e359 = local_544;
        let _e361 = select(_e359, 0f, (_e359 != _e359));
        local_545 = select(u32(clamp(_e361, -2147483600f, 2147483500f)), 2147483647u, (_e361 >= 2147483600f));
        let _e366 = local_545;
        local_546 = _e366;
        let _e367 = local_516;
        let _e368 = local_505;
        local_547 = (_e367 + _e368);
        let _e370 = local_547;
        local_548 = floor(_e370);
        let _e372 = local_548;
        let _e374 = select(_e372, 0f, (_e372 != _e372));
        local_549 = select(u32(clamp(_e374, -2147483600f, 2147483500f)), 2147483647u, (_e374 >= 2147483600f));
        let _e379 = local_549;
        local_550 = _e379;
        let _e380 = local_550;
        local_551 = _e380;
        let _e381 = local_546;
        local_552 = _e381;
        loop {
            let _e382 = local_552;
            let _e383 = local_551;
            local_553 = select(0u, 1u, (bitcast<i32>(_e382) <= bitcast<i32>(_e383)));
            let _e388 = local_553;
            if (_e388 == 0u) {
                break;
            } else {
                let _e390 = local_542;
                local_554 = _e390;
                let _e391 = local_538;
                local_555 = _e391;
                loop {
                    let _e392 = local_555;
                    let _e393 = local_554;
                    local_556 = select(0u, 1u, (bitcast<i32>(_e392) <= bitcast<i32>(_e393)));
                    let _e398 = local_556;
                    if (_e398 == 0u) {
                        break;
                    }
                    let _e400 = local_496;
                    let _e401 = local_498;
                    let _e402 = local_555;
                    let _e403 = local_552;
                    let _e404 = tile_index(_e400, _e401, _e402, _e403);
                    local_557 = _e404;
                    let _e405 = local_557;
                    local_558 = _e405;
                    let _e406 = local_558;
                    local_559 = select(0u, 1u, (bitcast<i32>(_e406) >= bitcast<i32>(0u)));
                    local_560 = 1u;
                    let _e411 = local_559;
                    if (_e411 == 0u) {
                        local_560 = 0u;
                    } else {
                        let _e413 = local_558;
                        local_561 = _e413;
                        let _e414 = local_561;
                        local_562 = _e414;
                        let _e415 = local_562;
                        local_563 = (_e415 * 4u);
                        let _e417 = local_483;
                        let _e418 = local_563;
                        local_564 = (_e417 + _e418);
                        let _e420 = local_564;
                        let _e425 = tiles.member[(_e420 >> bitcast<u32>(2u))];
                        local_565 = _e425;
                        let _e426 = local_565;
                        local_566 = select(0u, 1u, (_e426 != 0u));
                        let _e429 = local_566;
                        if (_e429 == 0u) {
                            local_560 = 0u;
                        }
                    }
                    let _e431 = local_560;
                    if (_e431 == 0u) {
                    } else {
                        let _e433 = local_555;
                        local_567 = f32(_e433);
                        let _e435 = local_510;
                        let _e436 = local_567;
                        local_568 = max(_e435, _e436);
                        let _e438 = local_555;
                        local_569 = f32(_e438);
                        let _e440 = local_569;
                        local_570 = (_e440 + 1f);
                        let _e442 = local_568;
                        let _e443 = local_570;
                        local_571 = min(_e442, _e443);
                        let _e445 = local_571;
                        local_572 = _e445;
                        let _e446 = local_552;
                        local_573 = f32(_e446);
                        let _e448 = local_516;
                        let _e449 = local_573;
                        local_574 = max(_e448, _e449);
                        let _e451 = local_552;
                        local_575 = f32(_e451);
                        let _e453 = local_575;
                        local_576 = (_e453 + 1f);
                        let _e455 = local_574;
                        let _e456 = local_576;
                        local_577 = min(_e455, _e456);
                        let _e458 = local_577;
                        local_578 = _e458;
                        let _e459 = local_510;
                        let _e460 = local_572;
                        local_579 = (_e459 - _e460);
                        let _e462 = local_579;
                        local_580 = _e462;
                        let _e463 = local_516;
                        let _e464 = local_578;
                        local_581 = (_e463 - _e464);
                        let _e466 = local_581;
                        local_582 = _e466;
                        let _e467 = local_580;
                        let _e468 = local_580;
                        local_583 = (_e467 * _e468);
                        let _e470 = local_582;
                        let _e471 = local_582;
                        local_584 = (_e470 * _e471);
                        let _e473 = local_583;
                        let _e474 = local_584;
                        local_585 = (_e473 + _e474);
                        let _e476 = local_585;
                        local_586 = _e476;
                        let _e477 = local_586;
                        local_587 = select(0u, 1u, (_e477 > 0f));
                        local_588 = 1u;
                        let _e480 = local_587;
                        if (_e480 == 0u) {
                            local_588 = 0u;
                        } else {
                            let _e482 = local_505;
                            let _e483 = local_505;
                            local_589 = (_e482 * _e483);
                            let _e485 = local_586;
                            let _e486 = local_589;
                            local_590 = select(0u, 1u, (_e485 < _e486));
                            let _e489 = local_590;
                            if (_e489 == 0u) {
                                local_588 = 0u;
                            }
                        }
                        local_591 = 1u;
                        let _e491 = local_588;
                        if (_e491 == 0u) {
                            local_591 = 0u;
                        } else {
                            local_592 = 1u;
                            let _e493 = local_534;
                            if (_e493 == 0u) {
                            } else {
                                local_592 = 0u;
                            }
                            let _e495 = local_592;
                            if (_e495 == 0u) {
                                local_591 = 0u;
                            }
                        }
                        let _e497 = local_591;
                        if (_e497 == 0u) {
                        } else {
                            local_534 = select(0u, 1u, (1u != 0u));
                            let _e501 = local_586;
                            local_593 = sqrt(_e501);
                            let _e503 = local_593;
                            local_594 = _e503;
                            let _e504 = local_580;
                            let _e505 = local_594;
                            local_595 = (_e504 / _e505);
                            let _e507 = local_595;
                            local_596 = _e507;
                            let _e508 = local_582;
                            let _e509 = local_594;
                            local_597 = (_e508 / _e509);
                            let _e511 = local_597;
                            local_598 = _e511;
                            let _e512 = local_529;
                            let _e513 = local_596;
                            local_599 = (_e512 * _e513);
                            let _e515 = local_531;
                            let _e516 = local_598;
                            local_600 = (_e515 * _e516);
                            let _e518 = local_599;
                            let _e519 = local_600;
                            local_601 = (_e518 + _e519);
                            let _e521 = local_601;
                            local_602 = _e521;
                            let _e522 = local_602;
                            let _e523 = local_596;
                            local_603 = (_e522 * _e523);
                            let _e525 = local_529;
                            let _e526 = local_603;
                            local_604 = (_e525 - _e526);
                            let _e528 = local_604;
                            let _e529 = local_487;
                            local_605 = (_e528 * _e529);
                            let _e531 = local_532;
                            let _e532 = local_605;
                            local_606 = (_e531 + _e532);
                            let _e534 = local_606;
                            local_532 = _e534;
                            let _e535 = local_602;
                            let _e536 = local_598;
                            local_607 = (_e535 * _e536);
                            let _e538 = local_531;
                            let _e539 = local_607;
                            local_608 = (_e538 - _e539);
                            let _e541 = local_608;
                            let _e542 = local_487;
                            local_609 = (_e541 * _e542);
                            let _e544 = local_533;
                            let _e545 = local_609;
                            local_610 = (_e544 + _e545);
                            let _e547 = local_610;
                            local_533 = _e547;
                            let _e548 = local_602;
                            local_611 = select(0u, 1u, (_e548 > 0f));
                            let _e551 = local_611;
                            if (_e551 == 0u) {
                            } else {
                                let _e553 = local_602;
                                let _e554 = local_596;
                                local_612 = (_e553 * _e554);
                                let _e556 = local_612;
                                let _e557 = local_488;
                                local_613 = (_e556 * _e557);
                                let _e559 = local_532;
                                let _e560 = local_613;
                                local_614 = (_e559 + _e560);
                                let _e562 = local_614;
                                local_532 = _e562;
                                let _e563 = local_602;
                                let _e564 = local_598;
                                local_615 = (_e563 * _e564);
                                let _e566 = local_615;
                                let _e567 = local_488;
                                local_616 = (_e566 * _e567);
                                let _e569 = local_533;
                                let _e570 = local_616;
                                local_617 = (_e569 + _e570);
                                let _e572 = local_617;
                                local_533 = _e572;
                            }
                        }
                    }
                    let _e573 = local_555;
                    local_618 = _e573;
                    let _e574 = local_555;
                    local_619 = (_e574 + 1u);
                    let _e576 = local_619;
                    local_555 = _e576;
                    continue;
                }
                let _e577 = local_552;
                local_620 = _e577;
                let _e578 = local_552;
                local_621 = (_e578 + 1u);
                let _e580 = local_621;
                local_552 = _e580;
                continue;
            }
        }
        let _e581 = local_521;
        let _e582 = local_532;
        local_622 = (_e581 + _e582);
        let _e584 = local_494;
        local_623 = _e584;
        let _e585 = local_623;
        local_624 = (_e585 * 4u);
        let _e587 = local_481;
        let _e588 = local_624;
        local_625 = (_e587 + _e588);
        let _e590 = local_625;
        let _e595 = local_622;
        previous_positions_1.member[(_e590 >> bitcast<u32>(2u))] = _e595;
        let _e596 = local_527;
        let _e597 = local_533;
        local_626 = (_e596 + _e597);
        let _e599 = local_494;
        local_627 = (_e599 + 1u);
        let _e601 = local_627;
        local_628 = _e601;
        let _e602 = local_628;
        local_629 = (_e602 * 4u);
        let _e604 = local_481;
        let _e605 = local_629;
        local_630 = (_e604 + _e605);
        let _e607 = local_630;
        let _e612 = local_626;
        previous_positions_1.member[(_e607 >> bitcast<u32>(2u))] = _e612;
        return;
    } else {
        return;
    }
}

fn raycast_1() {
    var local_631: u32;
    var local_632: u32;
    var local_633: u32;
    var local_634: u32;
    var local_635: u32;
    var local_636: u32;
    var local_637: u32;
    var local_638: u32;
    var local_639: u32;
    var local_640: u32;
    var local_641: u32;
    var local_642: u32;
    var local_643: u32;
    var local_644: u32;
    var local_645: u32;
    var local_646: u32;
    var local_647: u32;
    var local_648: u32;
    var local_649: u32;
    var local_650: u32;
    var local_651: u32;
    var local_652: u32;
    var local_653: f32;
    var local_654: f32;
    var local_655: u32;
    var local_656: u32;
    var local_657: u32;
    var local_658: u32;
    var local_659: f32;
    var local_660: f32;
    var local_661: u32;
    var local_662: u32;
    var local_663: u32;
    var local_664: u32;
    var local_665: f32;
    var local_666: f32;
    var local_667: u32;
    var local_668: u32;
    var local_669: u32;
    var local_670: u32;
    var local_671: f32;
    var local_672: f32;
    var local_673: u32;
    var local_674: u32;
    var local_675: u32;
    var local_676: u32;
    var local_677: f32;
    var local_678: f32;
    var local_679: f32;
    var local_680: f32;
    var local_681: u32;
    var local_682: f32;
    var local_683: f32;
    var local_684: u32;
    var local_685: u32;
    var local_686: u32;
    var local_687: u32;
    var local_688: u32;
    var local_689: u32;
    var local_690: u32;
    var local_691: u32;
    var local_692: f32;
    var local_693: u32;
    var local_694: u32;
    var local_695: f32;
    var local_696: u32;
    var local_697: u32;
    var local_698: u32;
    var local_699: u32;
    var local_700: f32;
    var local_701: f32;
    var local_702: f32;
    var local_703: f32;
    var local_704: u32;
    var local_705: f32;
    var local_706: f32;
    var local_707: f32;
    var local_708: f32;
    var local_709: f32;
    var local_710: u32;
    var local_711: f32;
    var local_712: f32;
    var local_713: f32;
    var local_714: f32;
    var local_715: f32;
    var local_716: u32;
    var local_717: f32;
    var local_718: f32;
    var local_719: f32;
    var local_720: f32;
    var local_721: f32;
    var local_722: u32;
    var local_723: f32;
    var local_724: f32;
    var local_725: f32;
    var local_726: f32;
    var local_727: f32;
    var local_728: f32;
    var local_729: u32;
    var local_730: u32;
    var local_731: u32;
    var local_732: u32;
    var local_733: u32;
    var local_734: u32;
    var local_735: u32;
    var local_736: u32;
    var local_737: u32;
    var local_738: u32;
    var local_739: u32;
    var local_740: u32;
    var local_741: u32;
    var local_742: u32;
    var local_743: u32;
    var local_744: u32;
    var local_745: u32;
    var local_746: u32;
    var local_747: u32;
    var local_748: u32;
    var local_749: f32;
    var local_750: f32;
    var local_751: u32;
    var local_752: f32;
    var local_753: f32;
    var local_754: u32;
    var local_755: f32;
    var local_756: u32;
    var local_757: f32;
    var local_758: u32;
    var local_759: u32;
    var local_760: u32;
    var local_761: u32;
    var local_762: u32;
    var local_763: u32;
    var local_764: u32;
    var local_765: u32;
    var local_766: u32;
    var local_767: u32;
    var local_768: u32;
    var local_769: u32;
    var local_770: u32;
    var local_771: u32;
    var local_772: u32;
    var local_773: u32;
    var local_774: u32;
    var local_775: u32;
    var local_776: u32;
    var local_777: u32;
    var local_778: u32;
    var local_779: u32;
    var local_780: f32;
    var local_781: f32;
    var local_782: u32;
    var local_783: u32;
    var local_784: u32;
    var local_785: u32;
    var local_786: u32;
    var local_787: u32;
    var local_788: f32;
    var local_789: f32;
    var local_790: u32;
    var local_791: u32;
    var local_792: u32;
    var local_793: u32;
    var local_794: f32;
    var local_795: f32;
    var local_796: f32;
    var local_797: f32;
    var local_798: f32;
    var local_799: f32;
    var local_800: f32;
    var local_801: f32;
    var local_802: f32;
    var local_803: f32;
    var local_804: f32;
    var local_805: f32;
    var local_806: f32;
    var local_807: f32;
    var local_808: f32;
    var local_809: f32;
    var local_810: f32;
    var local_811: f32;
    var local_812: f32;
    var local_813: u32;
    var local_814: f32;
    var local_815: f32;
    var local_816: f32;
    var local_817: f32;
    var local_818: f32;
    var local_819: u32;
    var local_820: u32;
    var local_821: u32;
    var local_822: u32;
    var local_823: f32;
    var local_824: f32;
    var local_825: f32;
    var local_826: f32;
    var local_827: f32;
    var local_828: f32;
    var local_829: f32;
    var local_830: f32;
    var local_831: f32;
    var local_832: f32;
    var local_833: u32;
    var local_834: u32;
    var local_835: u32;
    var local_836: u32;
    var local_837: u32;
    var local_838: u32;
    var local_839: u32;
    var local_840: u32;
    var local_841: u32;
    var local_842: u32;
    var local_843: u32;
    var local_844: u32;
    var local_845: u32;
    var local_846: u32;
    var local_847: u32;
    var local_848: u32;
    var local_849: u32;
    var local_850: u32;
    var local_851: u32;
    var local_852: u32;
    var local_853: u32;
    var local_854: u32;
    var local_855: u32;
    var local_856: u32;
    var local_857: u32;
    var local_858: u32;
    var local_859: u32;
    var local_860: u32;

    local_631 = 0u;
    local_632 = 0u;
    local_633 = 0u;
    local_634 = 0u;
    local_635 = 0u;
    local_636 = 0u;
    local_637 = 0u;
    let _e299 = raycast_args.tiles_w;
    local_638 = _e299;
    let _e301 = raycast_args.tiles_h;
    local_639 = _e301;
    let _e303 = raycast_args.num_circles;
    local_640 = _e303;
    let _e305 = raycast_args.num_rays;
    local_641 = _e305;
    let _e307 = raycast_args.mask;
    local_642 = _e307;
    let _e309 = raycast_args.ignore_group;
    local_643 = _e309;
    let _e311 = gl_GlobalInvocationId_6[0u];
    local_644 = _e311;
    let _e312 = local_644;
    local_645 = _e312;
    let _e313 = local_645;
    let _e314 = local_641;
    local_646 = select(0u, 1u, (_e313 >= _e314));
    let _e317 = local_646;
    if (_e317 == 0u) {
    } else {
        return;
    }
    let _e319 = local_645;
    local_647 = (_e319 * 8u);
    let _e321 = local_647;
    local_648 = _e321;
    let _e322 = local_648;
    local_649 = _e322;
    let _e323 = local_649;
    local_650 = _e323;
    let _e324 = local_650;
    local_651 = (_e324 * 4u);
    let _e326 = local_635;
    let _e327 = local_651;
    local_652 = (_e326 + _e327);
    let _e329 = local_652;
    let _e334 = rays.member[(_e329 >> bitcast<u32>(2u))];
    local_653 = _e334;
    let _e335 = local_653;
    local_654 = _e335;
    let _e336 = local_649;
    local_655 = (_e336 + 1u);
    let _e338 = local_655;
    local_656 = _e338;
    let _e339 = local_656;
    local_657 = (_e339 * 4u);
    let _e341 = local_635;
    let _e342 = local_657;
    local_658 = (_e341 + _e342);
    let _e344 = local_658;
    let _e349 = rays.member[(_e344 >> bitcast<u32>(2u))];
    local_659 = _e349;
    let _e350 = local_659;
    local_660 = _e350;
    let _e351 = local_649;
    local_661 = (_e351 + 2u);
    let _e353 = local_661;
    local_662 = _e353;
    let _e354 = local_662;
    local_663 = (_e354 * 4u);
    let _e356 = local_635;
    let _e357 = local_663;
    local_664 = (_e356 + _e357);
    let _e359 = local_664;
    let _e364 = rays.member[(_e359 >> bitcast<u32>(2u))];
    local_665 = _e364;
    let _e365 = local_665;
    local_666 = _e365;
    let _e366 = local_649;
    local_667 = (_e366 + 3u);
    let _e368 = local_667;
    local_668 = _e368;
    let _e369 = local_668;
    local_669 = (_e369 * 4u);
    let _e371 = local_635;
    let _e372 = local_669;
    local_670 = (_e371 + _e372);
    let _e374 = local_670;
    let _e379 = rays.member[(_e374 >> bitcast<u32>(2u))];
    local_671 = _e379;
    let _e380 = local_671;
    local_672 = _e380;
    let _e381 = local_649;
    local_673 = (_e381 + 4u);
    let _e383 = local_673;
    local_674 = _e383;
    let _e384 = local_674;
    local_675 = (_e384 * 4u);
    let _e386 = local_635;
    let _e387 = local_675;
    local_676 = (_e386 + _e387);
    let _e389 = local_676;
    let _e394 = rays.member[(_e389 >> bitcast<u32>(2u))];
    local_677 = _e394;
    let _e395 = local_677;
    local_678 = _e395;
    let _e396 = local_678;
    local_679 = _e396;
    local_680 = 0f;
    local_681 = 0u;
    local_682 = 0f;
    local_683 = 0f;
    let _e397 = local_642;
    local_684 = (_e397 & 1u);
    let _e399 = local_684;
    local_685 = select(0u, 1u, (_e399 != 0u));
    local_686 = 1u;
    let _e402 = local_685;
    if (_e402 == 0u) {
        local_686 = 0u;
    } else {
        let _e404 = local_638;
        local_687 = select(0u, 1u, (_e404 > 0u));
        let _e407 = local_687;
        if (_e407 == 0u) {
            local_686 = 0u;
        }
    }
    let _e409 = local_686;
    if (_e409 == 0u) {
    } else {
        let _e411 = local_638;
        local_688 = _e411;
        let _e412 = local_688;
        local_689 = _e412;
        let _e413 = local_639;
        local_690 = _e413;
        let _e414 = local_690;
        local_691 = _e414;
        let _e415 = local_654;
        local_692 = floor(_e415);
        let _e417 = local_692;
        let _e419 = select(_e417, 0f, (_e417 != _e417));
        local_693 = select(u32(clamp(_e419, -2147483600f, 2147483500f)), 2147483647u, (_e419 >= 2147483600f));
        let _e424 = local_693;
        local_694 = _e424;
        let _e425 = local_660;
        local_695 = floor(_e425);
        let _e427 = local_695;
        let _e429 = select(_e427, 0f, (_e427 != _e427));
        local_696 = select(u32(clamp(_e429, -2147483600f, 2147483500f)), 2147483647u, (_e429 >= 2147483600f));
        let _e434 = local_696;
        local_697 = _e434;
        local_698 = 1u;
        local_699 = 1u;
        local_700 = 1000000000000000000000000000000f;
        local_701 = 1000000000000000000000000000000f;
        local_702 = 1000000000000000000000000000000f;
        local_703 = 1000000000000000000000000000000f;
        let _e435 = local_666;
        local_704 = select(0u, 1u, (_e435 > 0f));
        let _e438 = local_704;
        if (_e438 == 0u) {
        } else {
            let _e440 = local_666;
            local_705 = (1f / _e440);
            let _e442 = local_705;
            local_702 = _e442;
            let _e443 = local_694;
            local_706 = f32(_e443);
            let _e445 = local_706;
            local_707 = (_e445 + 1f);
            let _e447 = local_707;
            let _e448 = local_654;
            local_708 = (_e447 - _e448);
            let _e450 = local_708;
            let _e451 = local_666;
            local_709 = (_e450 / _e451);
            let _e453 = local_709;
            local_700 = _e453;
        }
        let _e454 = local_666;
        local_710 = select(0u, 1u, (_e454 < 0f));
        let _e457 = local_710;
        if (_e457 == 0u) {
        } else {
            local_698 = 4294967295u;
            let _e459 = local_666;
            local_711 = (-1f / _e459);
            let _e461 = local_711;
            local_702 = _e461;
            let _e462 = local_694;
            local_712 = f32(_e462);
            let _e464 = local_654;
            let _e465 = local_712;
            local_713 = (_e464 - _e465);
            let _e467 = local_666;
            local_714 = -(_e467);
            let _e469 = local_713;
            let _e470 = local_714;
            local_715 = (_e469 / _e470);
            let _e472 = local_715;
            local_700 = _e472;
        }
        let _e473 = local_672;
        local_716 = select(0u, 1u, (_e473 > 0f));
        let _e476 = local_716;
        if (_e476 == 0u) {
        } else {
            let _e478 = local_672;
            local_717 = (1f / _e478);
            let _e480 = local_717;
            local_703 = _e480;
            let _e481 = local_697;
            local_718 = f32(_e481);
            let _e483 = local_718;
            local_719 = (_e483 + 1f);
            let _e485 = local_719;
            let _e486 = local_660;
            local_720 = (_e485 - _e486);
            let _e488 = local_720;
            let _e489 = local_672;
            local_721 = (_e488 / _e489);
            let _e491 = local_721;
            local_701 = _e491;
        }
        let _e492 = local_672;
        local_722 = select(0u, 1u, (_e492 < 0f));
        let _e495 = local_722;
        if (_e495 == 0u) {
        } else {
            local_699 = 4294967295u;
            let _e497 = local_672;
            local_723 = (-1f / _e497);
            let _e499 = local_723;
            local_703 = _e499;
            let _e500 = local_697;
            local_724 = f32(_e500);
            let _e502 = local_660;
            let _e503 = local_724;
            local_725 = (_e502 - _e503);
            let _e505 = local_672;
            local_726 = -(_e505);
            let _e507 = local_725;
            let _e508 = local_726;
            local_727 = (_e507 / _e508);
            let _e510 = local_727;
            local_701 = _e510;
        }
        local_728 = 0f;
        local_729 = 0u;
        local_730 = 0u;
        let _e511 = local_689;
        let _e512 = local_691;
        local_731 = (_e511 + _e512);
        let _e514 = local_731;
        local_732 = (_e514 + 4u);
        let _e516 = local_732;
        local_733 = _e516;
        loop {
            let _e517 = local_730;
            let _e518 = local_733;
            local_734 = select(0u, 1u, (bitcast<i32>(_e517) < bitcast<i32>(_e518)));
            local_735 = 1u;
            let _e523 = local_734;
            if (_e523 == 0u) {
                local_735 = 0u;
            } else {
                let _e525 = local_728;
                let _e526 = local_679;
                local_736 = select(0u, 1u, (_e525 <= _e526));
                let _e529 = local_736;
                if (_e529 == 0u) {
                    local_735 = 0u;
                }
            }
            let _e531 = local_735;
            if (_e531 == 0u) {
                break;
            }
            let _e533 = local_689;
            let _e534 = local_691;
            let _e535 = local_694;
            let _e536 = local_697;
            let _e537 = tile_index(_e533, _e534, _e535, _e536);
            local_737 = _e537;
            let _e538 = local_737;
            local_738 = _e538;
            let _e539 = local_738;
            local_739 = select(0u, 1u, (bitcast<i32>(_e539) >= bitcast<i32>(0u)));
            local_740 = 1u;
            let _e544 = local_739;
            if (_e544 == 0u) {
                local_740 = 0u;
            } else {
                let _e546 = local_738;
                local_741 = _e546;
                let _e547 = local_741;
                local_742 = _e547;
                let _e548 = local_742;
                local_743 = (_e548 * 4u);
                let _e550 = local_634;
                let _e551 = local_743;
                local_744 = (_e550 + _e551);
                let _e553 = local_744;
                let _e558 = tiles_1.member[(_e553 >> bitcast<u32>(2u))];
                local_745 = _e558;
                let _e559 = local_745;
                local_746 = select(0u, 1u, (_e559 != 0u));
                let _e562 = local_746;
                if (_e562 == 0u) {
                    local_740 = 0u;
                }
            }
            let _e564 = local_740;
            if (_e564 == 0u) {
                let _e566 = local_700;
                let _e567 = local_701;
                local_754 = select(0u, 1u, (_e566 < _e567));
                let _e570 = local_754;
                if (_e570 == 0u) {
                    let _e572 = local_701;
                    local_728 = _e572;
                    let _e573 = local_701;
                    let _e574 = local_703;
                    local_757 = (_e573 + _e574);
                    let _e576 = local_757;
                    local_701 = _e576;
                    let _e577 = local_697;
                    let _e578 = local_699;
                    local_758 = (_e577 + _e578);
                    let _e580 = local_758;
                    local_697 = _e580;
                    local_729 = 2u;
                } else {
                    let _e581 = local_700;
                    local_728 = _e581;
                    let _e582 = local_700;
                    let _e583 = local_702;
                    local_755 = (_e582 + _e583);
                    let _e585 = local_755;
                    local_700 = _e585;
                    let _e586 = local_694;
                    let _e587 = local_698;
                    local_756 = (_e586 + _e587);
                    let _e589 = local_756;
                    local_694 = _e589;
                    local_729 = 1u;
                }
                let _e590 = local_730;
                local_759 = (_e590 + 1u);
                let _e592 = local_759;
                local_730 = _e592;
                continue;
            } else {
                let _e593 = local_728;
                local_679 = _e593;
                local_680 = 1f;
                let _e594 = local_738;
                local_747 = _e594;
                let _e595 = local_747;
                local_681 = _e595;
                let _e596 = local_729;
                local_748 = select(0u, 1u, (_e596 == 1u));
                let _e599 = local_748;
                if (_e599 == 0u) {
                } else {
                    let _e601 = local_698;
                    local_749 = f32(_e601);
                    let _e603 = local_749;
                    local_750 = -(_e603);
                    let _e605 = local_750;
                    local_682 = _e605;
                    local_683 = 0f;
                }
                let _e606 = local_729;
                local_751 = select(0u, 1u, (_e606 == 2u));
                let _e609 = local_751;
                if (_e609 == 0u) {
                } else {
                    local_682 = 0f;
                    let _e611 = local_699;
                    local_752 = f32(_e611);
                    let _e613 = local_752;
                    local_753 = -(_e613);
                    let _e615 = local_753;
                    local_683 = _e615;
                }
                break;
            }
        }
    }
    let _e616 = local_642;
    local_760 = (_e616 & 2u);
    let _e618 = local_760;
    local_761 = select(0u, 1u, (_e618 != 0u));
    let _e621 = local_761;
    if (_e621 == 0u) {
    } else {
        let _e623 = local_640;
        local_762 = _e623;
        local_763 = 0u;
        loop {
            let _e624 = local_763;
            let _e625 = local_762;
            local_764 = select(0u, 1u, (_e624 < _e625));
            let _e628 = local_764;
            if (_e628 == 0u) {
                break;
            }
            let _e630 = local_643;
            local_765 = select(0u, 1u, (_e630 != 0u));
            local_766 = 1u;
            let _e633 = local_765;
            if (_e633 == 0u) {
                local_766 = 0u;
            } else {
                let _e635 = local_763;
                local_767 = _e635;
                let _e636 = local_767;
                local_768 = _e636;
                let _e637 = local_768;
                local_769 = (_e637 * 4u);
                let _e639 = local_633;
                let _e640 = local_769;
                local_770 = (_e639 + _e640);
                let _e642 = local_770;
                let _e647 = groups_1.member[(_e642 >> bitcast<u32>(2u))];
                local_771 = _e647;
                let _e648 = local_771;
                let _e649 = local_643;
                local_772 = select(0u, 1u, (_e648 == _e649));
                let _e652 = local_772;
                if (_e652 == 0u) {
                    local_766 = 0u;
                }
            }
            let _e654 = local_766;
            local_773 = select(0u, 1u, (_e654 != 0u));
            local_774 = 1u;
            let _e657 = local_773;
            if (_e657 == 0u) {
            } else {
                local_774 = 0u;
            }
            let _e659 = local_774;
            if (_e659 == 0u) {
            } else {
                let _e661 = local_763;
                local_775 = (_e661 * 2u);
                let _e663 = local_775;
                local_776 = _e663;
                let _e664 = local_776;
                local_777 = _e664;
                let _e665 = local_777;
                local_778 = (_e665 * 4u);
                let _e667 = local_631;
                let _e668 = local_778;
                local_779 = (_e667 + _e668);
                let _e670 = local_779;
                let _e675 = positions_4.member[(_e670 >> bitcast<u32>(2u))];
                local_780 = _e675;
                let _e676 = local_780;
                local_781 = _e676;
                let _e677 = local_763;
                local_782 = (_e677 * 2u);
                let _e679 = local_782;
                local_783 = (_e679 + 1u);
                let _e681 = local_783;
                local_784 = _e681;
                let _e682 = local_784;
                local_785 = _e682;
                let _e683 = local_785;
                local_786 = (_e683 * 4u);
                let _e685 = local_631;
                let _e686 = local_786;
                local_787 = (_e685 + _e686);
                let _e688 = local_787;
                let _e693 = positions_4.member[(_e688 >> bitcast<u32>(2u))];
                local_788 = _e693;
                let _e694 = local_788;
                local_789 = _e694;
                let _e695 = local_763;
                local_790 = _e695;
                let _e696 = local_790;
                local_791 = _e696;
                let _e697 = local_791;
                local_792 = (_e697 * 4u);
                let _e699 = local_632;
                let _e700 = local_792;
                local_793 = (_e699 + _e700);
                let _e702 = local_793;
                let _e707 = radius_4.member[(_e702 >> bitcast<u32>(2u))];
                local_794 = _e707;
                let _e708 = local_794;
                local_795 = _e708;
                let _e709 = local_654;
                let _e710 = local_781;
                local_796 = (_e709 - _e710);
                let _e712 = local_796;
                local_797 = _e712;
                let _e713 = local_660;
                let _e714 = local_789;
                local_798 = (_e713 - _e714);
                let _e716 = local_798;
                local_799 = _e716;
                let _e717 = local_797;
                let _e718 = local_666;
                local_800 = (_e717 * _e718);
                let _e720 = local_799;
                let _e721 = local_672;
                local_801 = (_e720 * _e721);
                let _e723 = local_800;
                let _e724 = local_801;
                local_802 = (_e723 + _e724);
                let _e726 = local_802;
                local_803 = _e726;
                let _e727 = local_797;
                let _e728 = local_797;
                local_804 = (_e727 * _e728);
                let _e730 = local_799;
                let _e731 = local_799;
                local_805 = (_e730 * _e731);
                let _e733 = local_804;
                let _e734 = local_805;
                local_806 = (_e733 + _e734);
                let _e736 = local_795;
                let _e737 = local_795;
                local_807 = (_e736 * _e737);
                let _e739 = local_806;
                let _e740 = local_807;
                local_808 = (_e739 - _e740);
                let _e742 = local_808;
                local_809 = _e742;
                let _e743 = local_803;
                let _e744 = local_803;
                local_810 = (_e743 * _e744);
                let _e746 = local_810;
                let _e747 = local_809;
                local_811 = (_e746 - _e747);
                let _e749 = local_811;
                local_812 = _e749;
                let _e750 = local_812;
                local_813 = select(0u, 1u, (_e750 >= 0f));
                let _e753 = local_813;
                if (_e753 == 0u) {
                } else {
                    let _e755 = local_812;
                    local_814 = sqrt(_e755);
                    let _e757 = local_814;
                    local_815 = _e757;
                    let _e758 = local_803;
                    local_816 = -(_e758);
                    let _e760 = local_816;
                    let _e761 = local_815;
                    local_817 = (_e760 - _e761);
                    let _e763 = local_817;
                    local_818 = _e763;
                    let _e764 = local_809;
                    local_819 = select(0u, 1u, (_e764 < 0f));
                    let _e767 = local_819;
                    if (_e767 == 0u) {
                    } else {
                        local_818 = 0f;
                    }
                    let _e769 = local_818;
                    local_820 = select(0u, 1u, (_e769 >= 0f));
                    local_821 = 1u;
                    let _e772 = local_820;
                    if (_e772 == 0u) {
                        local_821 = 0u;
                    } else {
                        let _e774 = local_818;
                        let _e775 = local_679;
                        local_822 = select(0u, 1u, (_e774 < _e775));
                        let _e778 = local_822;
                        if (_e778 == 0u) {
                            local_821 = 0u;
                        }
                    }
                    let _e780 = local_821;
                    if (_e780 == 0u) {
                    } else {
                        let _e782 = local_818;
                        local_679 = _e782;
                        local_680 = 2f;
                        let _e783 = local_763;
                        local_681 = _e783;
                        let _e784 = local_666;
                        let _e785 = local_818;
                        local_823 = (_e784 * _e785);
                        let _e787 = local_654;
                        let _e788 = local_823;
                        local_824 = (_e787 + _e788);
                        let _e790 = local_824;
                        let _e791 = local_781;
                        local_825 = (_e790 - _e791);
                        let _e793 = local_825;
                        local_826 = _e793;
                        let _e794 = local_672;
                        let _e795 = local_818;
                        local_827 = (_e794 * _e795);
                        let _e797 = local_660;
                        let _e798 = local_827;
                        local_828 = (_e797 + _e798);
                        let _e800 = local_828;
                        let _e801 = local_789;
                        local_829 = (_e800 - _e801);
                        let _e803 = local_829;
                        local_830 = _e803;
                        let _e804 = local_826;
                        let _e805 = local_795;
                        local_831 = (_e804 / _e805);
                        let _e807 = local_831;
                        local_682 = _e807;
                        let _e808 = local_830;
                        let _e809 = local_795;
                        local_832 = (_e808 / _e809);
                        let _e811 = local_832;
                        local_683 = _e811;
                    }
                }
            }
            let _e812 = local_763;
            local_833 = _e812;
            let _e813 = local_763;
            local_834 = (_e813 + 1u);
            let _e815 = local_834;
            local_763 = _e815;
            continue;
        }
    }
    let _e816 = local_645;
    local_835 = (_e816 * 4u);
    let _e818 = local_835;
    local_836 = _e818;
    let _e819 = local_836;
    local_837 = _e819;
    let _e820 = local_680;
    local_838 = select(0u, 1u, (_e820 > 0f));
    let _e823 = local_838;
    if (_e823 == 0u) {
        let _e825 = local_837;
        local_842 = _e825;
        let _e826 = local_842;
        local_843 = (_e826 * 4u);
        let _e828 = local_636;
        let _e829 = local_843;
        local_844 = (_e828 + _e829);
        let _e831 = local_844;
        hits.member[(_e831 >> bitcast<u32>(2u))] = -1f;
    } else {
        let _e836 = local_837;
        local_839 = _e836;
        let _e837 = local_839;
        local_840 = (_e837 * 4u);
        let _e839 = local_636;
        let _e840 = local_840;
        local_841 = (_e839 + _e840);
        let _e842 = local_841;
        let _e847 = local_679;
        hits.member[(_e842 >> bitcast<u32>(2u))] = _e847;
    }
    let _e848 = local_837;
    local_845 = (_e848 + 1u);
    let _e850 = local_845;
    local_846 = _e850;
    let _e851 = local_846;
    local_847 = (_e851 * 4u);
    let _e853 = local_636;
    let _e854 = local_847;
    local_848 = (_e853 + _e854);
    let _e856 = local_848;
    let _e861 = local_682;
    hits.member[(_e856 >> bitcast<u32>(2u))] = _e861;
    let _e862 = local_837;
    local_849 = (_e862 + 2u);
    let _e864 = local_849;
    local_850 = _e864;
    let _e865 = local_850;
    local_851 = (_e865 * 4u);
    let _e867 = local_636;
    let _e868 = local_851;
    local_852 = (_e867 + _e868);
    let _e870 = local_852;
    let _e875 = local_683;
    hits.member[(_e870 >> bitcast<u32>(2u))] = _e875;
    let _e876 = local_837;
    local_853 = (_e876 + 3u);
    let _e878 = local_853;
    local_854 = _e878;
    let _e879 = local_854;
    local_855 = (_e879 * 4u);
    let _e881 = local_636;
    let _e882 = local_855;
    local_856 = (_e881 + _e882);
    let _e884 = local_856;
    let _e889 = local_680;
    hits.member[(_e884 >> bitcast<u32>(2u))] = _e889;
    let _e890 = local_645;
    local_857 = _e890;
    let _e891 = local_857;
    local_858 = _e891;
    let _e892 = local_858;
    local_859 = (_e892 * 4u);
    let _e894 = local_637;
    let _e895 = local_859;
    local_860 = (_e894 + _e895);
    let _e897 = local_860;
    let _e902 = local_681;
    hit_ids.member[(_e897 >> bitcast<u32>(2u))] = _e902;
    return;
}

fn sensor_count_1() {
    var local_861: u32;
    var local_862: u32;
    var local_863: u32;
    var local_864: u32;
    var local_865: u32;
    var local_866: u32;
    var local_867: u32;
    var local_868: u32;
    var local_869: u32;
    var local_870: u32;
    var local_871: u32;
    var local_872: u32;
    var local_873: u32;
    var local_874: u32;
    var local_875: u32;
    var local_876: u32;
    var local_877: f32;
    var local_878: f32;
    var local_879: u32;
    var local_880: u32;
    var local_881: u32;
    var local_882: u32;
    var local_883: u32;
    var local_884: u32;
    var local_885: f32;
    var local_886: f32;
    var local_887: u32;
    var local_888: u32;
    var local_889: u32;
    var local_890: u32;
    var local_891: f32;
    var local_892: f32;
    var local_893: u32;
    var local_894: u32;
    var local_895: u32;
    var local_896: u32;
    var local_897: u32;
    var local_898: u32;
    var local_899: u32;
    var local_900: u32;
    var local_901: u32;
    var local_902: u32;
    var local_903: u32;
    var local_904: u32;
    var local_905: u32;
    var local_906: u32;
    var local_907: u32;
    var local_908: u32;
    var local_909: u32;
    var local_910: u32;
    var local_911: u32;
    var local_912: u32;
    var local_913: u32;
    var local_914: u32;
    var local_915: u32;
    var local_916: u32;
    var local_917: u32;
    var local_918: u32;
    var local_919: u32;
    var local_920: u32;
    var local_921: f32;
    var local_922: f32;
    var local_923: u32;
    var local_924: u32;
    var local_925: u32;
    var local_926: u32;
    var local_927: f32;
    var local_928: f32;
    var local_929: u32;
    var local_930: u32;
    var local_931: u32;
    var local_932: u32;
    var local_933: f32;
    var local_934: f32;
    var local_935: u32;
    var local_936: u32;
    var local_937: u32;
    var local_938: u32;
    var local_939: f32;
    var local_940: f32;
    var local_941: u32;
    var local_942: u32;
    var local_943: f32;
    var local_944: f32;
    var local_945: f32;
    var local_946: f32;
    var local_947: f32;
    var local_948: f32;
    var local_949: f32;
    var local_950: f32;
    var local_951: f32;
    var local_952: f32;
    var local_953: u32;
    var local_954: f32;
    var local_955: f32;
    var local_956: f32;
    var local_957: f32;
    var local_958: f32;
    var local_959: f32;
    var local_960: f32;
    var local_961: f32;
    var local_962: f32;
    var local_963: f32;
    var local_964: f32;
    var local_965: f32;
    var local_966: f32;
    var local_967: f32;
    var local_968: f32;
    var local_969: f32;
    var local_970: f32;
    var local_971: f32;
    var local_972: u32;
    var local_973: u32;
    var local_974: u32;
    var local_975: u32;
    var local_976: u32;
    var local_977: u32;
    var local_978: u32;
    var local_979: u32;

    local_861 = 0u;
    local_862 = 0u;
    local_863 = 0u;
    local_864 = 0u;
    local_865 = 0u;
    local_866 = 0u;
    let _e188 = sensor_count_args.num_circles;
    local_867 = _e188;
    let _e190 = sensor_count_args.num_sensors;
    local_868 = _e190;
    let _e192 = gl_GlobalInvocationId_6[0u];
    local_869 = _e192;
    let _e193 = local_869;
    local_870 = _e193;
    let _e194 = local_870;
    let _e195 = local_867;
    local_871 = select(0u, 1u, (_e194 >= _e195));
    let _e198 = local_871;
    if (_e198 == 0u) {
        let _e200 = local_870;
        local_872 = (_e200 * 2u);
        let _e202 = local_872;
        local_873 = _e202;
        let _e203 = local_873;
        local_874 = _e203;
        let _e204 = local_874;
        local_875 = (_e204 * 4u);
        let _e206 = local_861;
        let _e207 = local_875;
        local_876 = (_e206 + _e207);
        let _e209 = local_876;
        let _e214 = positions_5.member[(_e209 >> bitcast<u32>(2u))];
        local_877 = _e214;
        let _e215 = local_877;
        local_878 = _e215;
        let _e216 = local_870;
        local_879 = (_e216 * 2u);
        let _e218 = local_879;
        local_880 = (_e218 + 1u);
        let _e220 = local_880;
        local_881 = _e220;
        let _e221 = local_881;
        local_882 = _e221;
        let _e222 = local_882;
        local_883 = (_e222 * 4u);
        let _e224 = local_861;
        let _e225 = local_883;
        local_884 = (_e224 + _e225);
        let _e227 = local_884;
        let _e232 = positions_5.member[(_e227 >> bitcast<u32>(2u))];
        local_885 = _e232;
        let _e233 = local_885;
        local_886 = _e233;
        let _e234 = local_870;
        local_887 = _e234;
        let _e235 = local_887;
        local_888 = _e235;
        let _e236 = local_888;
        local_889 = (_e236 * 4u);
        let _e238 = local_862;
        let _e239 = local_889;
        local_890 = (_e238 + _e239);
        let _e241 = local_890;
        let _e246 = radius_5.member[(_e241 >> bitcast<u32>(2u))];
        local_891 = _e246;
        let _e247 = local_891;
        local_892 = _e247;
        let _e248 = local_870;
        local_893 = _e248;
        let _e249 = local_893;
        local_894 = _e249;
        let _e250 = local_894;
        local_895 = (_e250 * 4u);
        let _e252 = local_863;
        let _e253 = local_895;
        local_896 = (_e252 + _e253);
        let _e255 = local_896;
        let _e260 = tags_1.member[(_e255 >> bitcast<u32>(2u))];
        local_897 = _e260;
        let _e261 = local_897;
        local_898 = _e261;
        let _e262 = local_868;
        local_899 = _e262;
        local_900 = 0u;
        loop {
            let _e263 = local_900;
            let _e264 = local_899;
            local_901 = select(0u, 1u, (_e263 < _e264));
            let _e267 = local_901;
            if (_e267 == 0u) {
                break;
            }
            let _e269 = local_900;
            local_902 = _e269;
            let _e270 = local_902;
            local_903 = _e270;
            let _e271 = local_903;
            local_904 = (_e271 * 4u);
            let _e273 = local_865;
            let _e274 = local_904;
            local_905 = (_e273 + _e274);
            let _e276 = local_905;
            let _e281 = sensor_mask.member[(_e276 >> bitcast<u32>(2u))];
            local_906 = _e281;
            let _e282 = local_906;
            local_907 = _e282;
            let _e283 = local_907;
            local_908 = select(0u, 1u, (_e283 == 0u));
            local_909 = 0u;
            let _e286 = local_908;
            if (_e286 != 0u) {
                local_909 = 1u;
            } else {
                let _e288 = local_898;
                local_910 = (_e288 & 31u);
                let _e290 = local_907;
                let _e291 = local_910;
                local_911 = (_e290 >> bitcast<u32>((_e291 & 31u)));
                let _e295 = local_911;
                local_912 = (_e295 & 1u);
                let _e297 = local_912;
                local_913 = select(0u, 1u, (_e297 != 0u));
                let _e300 = local_913;
                if (_e300 != 0u) {
                    local_909 = 1u;
                }
            }
            let _e302 = local_909;
            local_914 = select(0u, 1u, (_e302 != 0u));
            let _e305 = local_914;
            if (_e305 == 0u) {
            } else {
                let _e307 = local_900;
                local_915 = (_e307 * 4u);
                let _e309 = local_915;
                local_916 = _e309;
                let _e310 = local_916;
                local_917 = _e310;
                let _e311 = local_917;
                local_918 = _e311;
                let _e312 = local_918;
                local_919 = (_e312 * 4u);
                let _e314 = local_864;
                let _e315 = local_919;
                local_920 = (_e314 + _e315);
                let _e317 = local_920;
                let _e322 = sensors.member[(_e317 >> bitcast<u32>(2u))];
                local_921 = _e322;
                let _e323 = local_921;
                local_922 = _e323;
                let _e324 = local_917;
                local_923 = (_e324 + 1u);
                let _e326 = local_923;
                local_924 = _e326;
                let _e327 = local_924;
                local_925 = (_e327 * 4u);
                let _e329 = local_864;
                let _e330 = local_925;
                local_926 = (_e329 + _e330);
                let _e332 = local_926;
                let _e337 = sensors.member[(_e332 >> bitcast<u32>(2u))];
                local_927 = _e337;
                let _e338 = local_927;
                local_928 = _e338;
                let _e339 = local_917;
                local_929 = (_e339 + 2u);
                let _e341 = local_929;
                local_930 = _e341;
                let _e342 = local_930;
                local_931 = (_e342 * 4u);
                let _e344 = local_864;
                let _e345 = local_931;
                local_932 = (_e344 + _e345);
                let _e347 = local_932;
                let _e352 = sensors.member[(_e347 >> bitcast<u32>(2u))];
                local_933 = _e352;
                let _e353 = local_933;
                local_934 = _e353;
                let _e354 = local_917;
                local_935 = (_e354 + 3u);
                let _e356 = local_935;
                local_936 = _e356;
                let _e357 = local_936;
                local_937 = (_e357 * 4u);
                let _e359 = local_864;
                let _e360 = local_937;
                local_938 = (_e359 + _e360);
                let _e362 = local_938;
                let _e367 = sensors.member[(_e362 >> bitcast<u32>(2u))];
                local_939 = _e367;
                let _e368 = local_939;
                local_940 = _e368;
                local_941 = select(0u, 1u, (0u != 0u));
                let _e371 = local_940;
                local_942 = select(0u, 1u, (_e371 < 0f));
                let _e374 = local_942;
                if (_e374 == 0u) {
                    let _e376 = local_922;
                    let _e377 = local_934;
                    local_954 = (_e376 - _e377);
                    let _e379 = local_878;
                    let _e380 = local_954;
                    local_955 = max(_e379, _e380);
                    let _e382 = local_922;
                    let _e383 = local_934;
                    local_956 = (_e382 + _e383);
                    let _e385 = local_955;
                    let _e386 = local_956;
                    local_957 = min(_e385, _e386);
                    let _e388 = local_957;
                    local_958 = _e388;
                    let _e389 = local_928;
                    let _e390 = local_940;
                    local_959 = (_e389 - _e390);
                    let _e392 = local_886;
                    let _e393 = local_959;
                    local_960 = max(_e392, _e393);
                    let _e395 = local_928;
                    let _e396 = local_940;
                    local_961 = (_e395 + _e396);
                    let _e398 = local_960;
                    let _e399 = local_961;
                    local_962 = min(_e398, _e399);
                    let _e401 = local_962;
                    local_963 = _e401;
                    let _e402 = local_878;
                    let _e403 = local_958;
                    local_964 = (_e402 - _e403);
                    let _e405 = local_964;
                    local_965 = _e405;
                    let _e406 = local_886;
                    let _e407 = local_963;
                    local_966 = (_e406 - _e407);
                    let _e409 = local_966;
                    local_967 = _e409;
                    let _e410 = local_965;
                    let _e411 = local_965;
                    local_968 = (_e410 * _e411);
                    let _e413 = local_967;
                    let _e414 = local_967;
                    local_969 = (_e413 * _e414);
                    let _e416 = local_968;
                    let _e417 = local_969;
                    local_970 = (_e416 + _e417);
                    let _e419 = local_892;
                    let _e420 = local_892;
                    local_971 = (_e419 * _e420);
                    let _e422 = local_970;
                    let _e423 = local_971;
                    local_972 = select(0u, 1u, (_e422 < _e423));
                    let _e426 = local_972;
                    local_941 = select(0u, 1u, (_e426 != 0u));
                } else {
                    let _e429 = local_878;
                    let _e430 = local_922;
                    local_943 = (_e429 - _e430);
                    let _e432 = local_943;
                    local_944 = _e432;
                    let _e433 = local_886;
                    let _e434 = local_928;
                    local_945 = (_e433 - _e434);
                    let _e436 = local_945;
                    local_946 = _e436;
                    let _e437 = local_934;
                    let _e438 = local_892;
                    local_947 = (_e437 + _e438);
                    let _e440 = local_947;
                    local_948 = _e440;
                    let _e441 = local_944;
                    let _e442 = local_944;
                    local_949 = (_e441 * _e442);
                    let _e444 = local_946;
                    let _e445 = local_946;
                    local_950 = (_e444 * _e445);
                    let _e447 = local_949;
                    let _e448 = local_950;
                    local_951 = (_e447 + _e448);
                    let _e450 = local_948;
                    let _e451 = local_948;
                    local_952 = (_e450 * _e451);
                    let _e453 = local_951;
                    let _e454 = local_952;
                    local_953 = select(0u, 1u, (_e453 < _e454));
                    let _e457 = local_953;
                    local_941 = select(0u, 1u, (_e457 != 0u));
                }
                let _e460 = local_941;
                if (_e460 == 0u) {
                } else {
                    let _e462 = local_900;
                    local_973 = _e462;
                    let _e463 = local_973;
                    local_974 = _e463;
                    let _e464 = local_974;
                    local_975 = (_e464 * 4u);
                    let _e466 = local_866;
                    let _e467 = local_975;
                    local_976 = (_e466 + _e467);
                    let _e469 = local_976;
                    let _e474 = atomicAdd((&sensor_counts.member[(_e469 >> bitcast<u32>(2u))]), 1u);
                    local_977 = _e474;
                }
            }
            let _e475 = local_900;
            local_978 = _e475;
            let _e476 = local_900;
            local_979 = (_e476 + 1u);
            let _e478 = local_979;
            local_900 = _e478;
            continue;
        }
        return;
    } else {
        return;
    }
}

@compute @workgroup_size(64, 1, 1) 
fn solve_joints(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>) {
    gl_GlobalInvocationId_6 = gl_GlobalInvocationId;
    solve_joints_1();
}

@compute @workgroup_size(64, 1, 1) 
fn solve_collisions_grouped(@builtin(global_invocation_id) gl_GlobalInvocationId_1: vec3<u32>) {
    gl_GlobalInvocationId_6 = gl_GlobalInvocationId_1;
    solve_collisions_grouped_1();
}

@compute @workgroup_size(64, 1, 1) 
fn integrate_tagged(@builtin(global_invocation_id) gl_GlobalInvocationId_2: vec3<u32>) {
    gl_GlobalInvocationId_6 = gl_GlobalInvocationId_2;
    integrate_tagged_1();
}

@compute @workgroup_size(64, 1, 1) 
fn tile_friction(@builtin(global_invocation_id) gl_GlobalInvocationId_3: vec3<u32>) {
    gl_GlobalInvocationId_6 = gl_GlobalInvocationId_3;
    tile_friction_1();
}

@compute @workgroup_size(64, 1, 1) 
fn raycast(@builtin(global_invocation_id) gl_GlobalInvocationId_4: vec3<u32>) {
    gl_GlobalInvocationId_6 = gl_GlobalInvocationId_4;
    raycast_1();
}

@compute @workgroup_size(64, 1, 1) 
fn sensor_count(@builtin(global_invocation_id) gl_GlobalInvocationId_5: vec3<u32>) {
    gl_GlobalInvocationId_6 = gl_GlobalInvocationId_5;
    sensor_count_1();
}
