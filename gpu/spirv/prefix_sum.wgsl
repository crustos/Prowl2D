struct data_buffer {
    member: array<u32>,
}

struct block_sums_buffer {
    member: array<u32>,
}

struct prefix_sum_of_each_block_push {
    total_elems: u32,
}

struct add_block_prefix_sums_to_the_buffer_push {
    total_elems: u32,
}

@group(0) @binding(0) 
var<storage, read_write> data: data_buffer;
@group(0) @binding(1) 
var<storage, read_write> block_sums: block_sums_buffer;
@group(0) @binding(30) 
var<uniform> prefix_sum_of_each_block_args: prefix_sum_of_each_block_push;
var<workgroup> SCAN: array<u32, 256>;
var<private> gl_GlobalInvocationId_3: vec3<u32>;
var<private> gl_LocalInvocationId_3: vec3<u32>;
var<private> gl_WorkgroupId_1: vec3<u32>;
@group(0) @binding(0) 
var<storage, read_write> data_1: data_buffer;
@group(0) @binding(1) 
var<storage, read_write> block_sums_1: block_sums_buffer;
@group(0) @binding(0) 
var<storage, read_write> data_2: data_buffer;
@group(0) @binding(1) 
var<storage, read_write> block_sums_2: block_sums_buffer;
@group(0) @binding(30) 
var<uniform> add_block_prefix_sums_to_the_buffer_args: add_block_prefix_sums_to_the_buffer_push;
var<workgroup> PREVIOUS_BLOCK_SUM: u32;

fn scan_block(param: u32) {
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

    local = param;
    local_1 = 1u;
    loop {
        let _e38 = local_1;
        local_2 = select(0u, 1u, (_e38 < 256u));
        let _e41 = local_2;
        if (_e41 == 0u) {
            break;
        }
        workgroupBarrier();
        local_3 = 0u;
        let _e43 = local;
        let _e44 = local_1;
        local_4 = select(0u, 1u, (_e43 >= _e44));
        let _e47 = local_4;
        if (_e47 == 0u) {
        } else {
            let _e49 = local;
            let _e50 = local_1;
            local_5 = (_e49 - _e50);
            let _e52 = local_5;
            local_6 = _e52;
            let _e53 = local_6;
            local_7 = _e53;
            let _e54 = local_7;
            let _e56 = SCAN[_e54];
            local_8 = _e56;
            let _e57 = local_8;
            local_3 = _e57;
        }
        workgroupBarrier();
        let _e58 = local;
        local_9 = _e58;
        let _e59 = local_9;
        local_10 = _e59;
        let _e60 = local_10;
        let _e62 = SCAN[_e60];
        local_11 = _e62;
        let _e63 = local_11;
        let _e64 = local_3;
        local_12 = (_e63 + _e64);
        let _e66 = local;
        local_13 = _e66;
        let _e67 = local_13;
        local_14 = _e67;
        let _e68 = local_14;
        let _e70 = local_12;
        SCAN[_e68] = _e70;
        let _e71 = local_1;
        local_15 = (_e71 << bitcast<u32>((1u & 31u)));
        let _e75 = local_15;
        local_1 = _e75;
        continue;
    }
    workgroupBarrier();
    return;
}

fn prefix_sum_of_each_block_1() {
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
    var local_33: u32;
    var local_34: u32;
    var local_35: u32;
    var local_36: u32;
    var local_37: u32;
    var local_38: u32;
    var local_39: u32;
    var local_40: u32;
    var local_41: u32;
    var local_42: u32;
    var local_43: u32;
    var local_44: u32;
    var local_45: u32;
    var local_46: u32;

    local_16 = 0u;
    local_17 = 0u;
    let _e53 = prefix_sum_of_each_block_args.total_elems;
    local_18 = _e53;
    let _e55 = gl_GlobalInvocationId_3[0u];
    local_19 = _e55;
    let _e56 = local_19;
    local_20 = _e56;
    let _e58 = gl_LocalInvocationId_3[0u];
    local_21 = _e58;
    let _e59 = local_21;
    local_22 = _e59;
    local_23 = 0u;
    let _e60 = local_20;
    let _e61 = local_18;
    local_24 = select(0u, 1u, (_e60 < _e61));
    let _e64 = local_24;
    if (_e64 == 0u) {
    } else {
        let _e66 = local_20;
        local_25 = _e66;
        let _e67 = local_25;
        local_26 = _e67;
        let _e68 = local_26;
        local_27 = (_e68 * 4u);
        let _e70 = local_16;
        let _e71 = local_27;
        local_28 = (_e70 + _e71);
        let _e73 = local_28;
        let _e78 = data.member[(_e73 >> bitcast<u32>(2u))];
        local_29 = _e78;
        let _e79 = local_29;
        local_23 = _e79;
    }
    let _e80 = local_22;
    local_30 = _e80;
    let _e81 = local_30;
    local_31 = _e81;
    let _e82 = local_31;
    let _e84 = local_23;
    SCAN[_e82] = _e84;
    let _e85 = local_22;
    scan_block(_e85);
    local_32 = 0u;
    let _e86 = local_22;
    local_33 = _e86;
    let _e87 = local_33;
    local_34 = _e87;
    let _e88 = local_34;
    let _e90 = SCAN[_e88];
    local_35 = _e90;
    let _e91 = local_35;
    local_32 = _e91;
    let _e92 = local_20;
    let _e93 = local_18;
    local_36 = select(0u, 1u, (_e92 < _e93));
    let _e96 = local_36;
    if (_e96 == 0u) {
    } else {
        let _e98 = local_22;
        local_37 = select(0u, 1u, (_e98 == 255u));
        let _e101 = local_37;
        if (_e101 == 0u) {
        } else {
            let _e104 = gl_WorkgroupId_1[0u];
            local_38 = _e104;
            let _e105 = local_38;
            local_39 = _e105;
            let _e106 = local_39;
            local_40 = _e106;
            let _e107 = local_40;
            local_41 = (_e107 * 4u);
            let _e109 = local_17;
            let _e110 = local_41;
            local_42 = (_e109 + _e110);
            let _e112 = local_42;
            let _e117 = local_32;
            block_sums.member[(_e112 >> bitcast<u32>(2u))] = _e117;
        }
        let _e118 = local_20;
        local_43 = _e118;
        let _e119 = local_43;
        local_44 = _e119;
        let _e120 = local_44;
        local_45 = (_e120 * 4u);
        let _e122 = local_16;
        let _e123 = local_45;
        local_46 = (_e122 + _e123);
        let _e125 = local_46;
        let _e130 = local_32;
        data.member[(_e125 >> bitcast<u32>(2u))] = _e130;
    }
    return;
}

fn prefix_sum_of_the_block_sums_1() {
    var local_47: u32;
    var local_48: u32;
    var local_49: u32;
    var local_50: u32;
    var local_51: u32;
    var local_52: u32;
    var local_53: u32;
    var local_54: u32;
    var local_55: u32;
    var local_56: u32;
    var local_57: u32;
    var local_58: u32;
    var local_59: u32;
    var local_60: u32;
    var local_61: u32;
    var local_62: u32;
    var local_63: u32;
    var local_64: u32;
    var local_65: u32;
    var local_66: u32;

    local_47 = 0u;
    local_48 = 0u;
    let _e42 = gl_GlobalInvocationId_3[0u];
    local_49 = _e42;
    let _e43 = local_49;
    local_50 = _e43;
    let _e45 = gl_LocalInvocationId_3[0u];
    local_51 = _e45;
    let _e46 = local_51;
    local_52 = _e46;
    let _e47 = local_50;
    local_53 = _e47;
    let _e48 = local_53;
    local_54 = _e48;
    let _e49 = local_54;
    local_55 = (_e49 * 4u);
    let _e51 = local_48;
    let _e52 = local_55;
    local_56 = (_e51 + _e52);
    let _e54 = local_56;
    let _e59 = block_sums_1.member[(_e54 >> bitcast<u32>(2u))];
    local_57 = _e59;
    let _e60 = local_52;
    local_58 = _e60;
    let _e61 = local_58;
    local_59 = _e61;
    let _e62 = local_59;
    let _e64 = local_57;
    SCAN[_e62] = _e64;
    let _e65 = local_52;
    scan_block(_e65);
    let _e66 = local_52;
    local_60 = _e66;
    let _e67 = local_60;
    local_61 = _e67;
    let _e68 = local_61;
    let _e70 = SCAN[_e68];
    local_62 = _e70;
    let _e71 = local_50;
    local_63 = _e71;
    let _e72 = local_63;
    local_64 = _e72;
    let _e73 = local_64;
    local_65 = (_e73 * 4u);
    let _e75 = local_48;
    let _e76 = local_65;
    local_66 = (_e75 + _e76);
    let _e78 = local_66;
    let _e83 = local_62;
    block_sums_1.member[(_e78 >> bitcast<u32>(2u))] = _e83;
    return;
}

fn add_block_prefix_sums_to_the_buffer_1() {
    var local_67: u32;
    var local_68: u32;
    var local_69: u32;
    var local_70: u32;
    var local_71: u32;
    var local_72: u32;
    var local_73: u32;
    var local_74: u32;
    var local_75: u32;
    var local_76: u32;
    var local_77: u32;
    var local_78: u32;
    var local_79: u32;
    var local_80: u32;
    var local_81: u32;
    var local_82: u32;
    var local_83: u32;
    var local_84: u32;
    var local_85: u32;
    var local_86: u32;
    var local_87: u32;
    var local_88: u32;
    var local_89: u32;
    var local_90: u32;
    var local_91: u32;
    var local_92: u32;
    var local_93: u32;
    var local_94: u32;
    var local_95: u32;
    var local_96: u32;

    local_67 = 0u;
    local_68 = 0u;
    let _e52 = add_block_prefix_sums_to_the_buffer_args.total_elems;
    local_69 = _e52;
    let _e54 = gl_GlobalInvocationId_3[0u];
    local_70 = _e54;
    let _e55 = local_70;
    local_71 = _e55;
    let _e57 = gl_LocalInvocationId_3[0u];
    local_72 = _e57;
    let _e58 = local_72;
    local_73 = _e58;
    let _e59 = local_71;
    local_74 = (_e59 / 256u);
    let _e61 = local_74;
    local_75 = _e61;
    let _e62 = local_73;
    local_76 = select(0u, 1u, (_e62 == 0u));
    let _e65 = local_76;
    if (_e65 == 0u) {
    } else {
        let _e67 = local_75;
        local_77 = select(0u, 1u, (_e67 > 0u));
        let _e70 = local_77;
        if (_e70 == 0u) {
        } else {
            let _e72 = local_71;
            let _e73 = local_69;
            local_78 = select(0u, 1u, (_e72 < _e73));
            let _e76 = local_78;
            if (_e76 == 0u) {
            } else {
                let _e78 = local_75;
                local_79 = (_e78 - 1u);
                let _e80 = local_79;
                local_80 = _e80;
                let _e81 = local_80;
                local_81 = _e81;
                let _e82 = local_81;
                local_82 = (_e82 * 4u);
                let _e84 = local_68;
                let _e85 = local_82;
                local_83 = (_e84 + _e85);
                let _e87 = local_83;
                let _e92 = block_sums_2.member[(_e87 >> bitcast<u32>(2u))];
                local_84 = _e92;
                let _e93 = local_84;
                PREVIOUS_BLOCK_SUM = _e93;
            }
        }
    }
    workgroupBarrier();
    let _e94 = local_71;
    let _e95 = local_69;
    local_85 = select(0u, 1u, (_e94 < _e95));
    let _e98 = local_85;
    if (_e98 == 0u) {
    } else {
        let _e100 = local_75;
        local_86 = select(0u, 1u, (_e100 > 0u));
        let _e103 = local_86;
        if (_e103 == 0u) {
        } else {
            let _e105 = local_71;
            local_87 = _e105;
            let _e106 = local_87;
            local_88 = _e106;
            let _e107 = local_88;
            local_89 = (_e107 * 4u);
            let _e109 = local_67;
            let _e110 = local_89;
            local_90 = (_e109 + _e110);
            let _e112 = local_90;
            let _e117 = data_2.member[(_e112 >> bitcast<u32>(2u))];
            local_91 = _e117;
            let _e118 = local_91;
            let _e119 = PREVIOUS_BLOCK_SUM;
            local_92 = (_e118 + _e119);
            let _e121 = local_71;
            local_93 = _e121;
            let _e122 = local_93;
            local_94 = _e122;
            let _e123 = local_94;
            local_95 = (_e123 * 4u);
            let _e125 = local_67;
            let _e126 = local_95;
            local_96 = (_e125 + _e126);
            let _e128 = local_96;
            let _e133 = local_92;
            data_2.member[(_e128 >> bitcast<u32>(2u))] = _e133;
        }
    }
    return;
}

@compute @workgroup_size(256, 1, 1) 
fn prefix_sum_of_each_block(@builtin(global_invocation_id) gl_GlobalInvocationId: vec3<u32>, @builtin(local_invocation_id) gl_LocalInvocationId: vec3<u32>, @builtin(workgroup_id) gl_WorkgroupId: vec3<u32>) {
    gl_GlobalInvocationId_3 = gl_GlobalInvocationId;
    gl_LocalInvocationId_3 = gl_LocalInvocationId;
    gl_WorkgroupId_1 = gl_WorkgroupId;
    prefix_sum_of_each_block_1();
}

@compute @workgroup_size(256, 1, 1) 
fn prefix_sum_of_the_block_sums(@builtin(global_invocation_id) gl_GlobalInvocationId_1: vec3<u32>, @builtin(local_invocation_id) gl_LocalInvocationId_1: vec3<u32>) {
    gl_GlobalInvocationId_3 = gl_GlobalInvocationId_1;
    gl_LocalInvocationId_3 = gl_LocalInvocationId_1;
    prefix_sum_of_the_block_sums_1();
}

@compute @workgroup_size(256, 1, 1) 
fn add_block_prefix_sums_to_the_buffer(@builtin(global_invocation_id) gl_GlobalInvocationId_2: vec3<u32>, @builtin(local_invocation_id) gl_LocalInvocationId_2: vec3<u32>) {
    gl_GlobalInvocationId_3 = gl_GlobalInvocationId_2;
    gl_LocalInvocationId_3 = gl_LocalInvocationId_2;
    add_block_prefix_sums_to_the_buffer_1();
}
